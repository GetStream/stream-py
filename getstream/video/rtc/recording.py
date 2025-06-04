"""
Audio recorder

This module provides audio recording capabilities with:
- Individual user recording (separate files per user)
- Composite recording (mixed audio of all users)
"""

import logging
import threading
import time
import wave
from collections import defaultdict
from enum import Enum
from pathlib import Path
from typing import Dict, List, Optional, Set, Union
import os

import numpy as np

logger = logging.getLogger(__name__)


class RecordingType(Enum):
    TRACK = "track"
    COMPOSITE = "composite"


class AudioRecorder:
    
    def __init__(self, output_dir: str = "recordings"):
        """
        Initialize the audio recorder.
        
        Args:
            output_dir: Default directory for recording files
        """
        # Recording state
        self._recording_types: Set[RecordingType] = set()
        self._target_user_ids: Optional[Set[str]] = None
        self._output_dir = Path(output_dir)
        
        self._recording_files: Dict[str, wave.Wave_write] = {}
        self._composite_recording_file: Optional[wave.Wave_write] = None
        
        self._timestamp_frame_map: Dict[float, List[Dict]] = defaultdict(list)  # timestamp -> list of frames
        self._user_start_times: Dict[str, float] = {}  # user_id -> time when first frame was recorded
        self._reference_start_time: Optional[float] = None  # timestamp of the very first frame
        self._recording_start_time: Optional[float] = None  # when recording actually started
        
        self._frame_duration = 0.02  # 20ms frame duration (standard for WebRTC)
        self._max_timestamp_gap = 1.0  # Maximum gap to keep in timestamp map (1 second)
        self._processed_timestamp = 0.0  # Last timestamp that was written to file
        
        self._recording_lock = threading.Lock()
        self._composite_lock = threading.Lock()
        
        self.AUDIO_SAMPLE_RATE = 48000
        self.AUDIO_CHANNELS = 1
        self.AUDIO_SAMPLE_WIDTH = 2  # 16-bit
        self.SAMPLES_PER_FRAME = int(self.AUDIO_SAMPLE_RATE * self._frame_duration)  # 960 samples for 20ms
    
    @property
    def is_recording(self) -> bool:
        """Check if any recording is currently active."""
        return len(self._recording_types) > 0
    
    @property
    def recording_types(self) -> Set[RecordingType]:
        """Get currently active recording types."""
        return self._recording_types.copy()
    
    def start_recording(
        self,
        recording_types: List[RecordingType],
        user_ids: Optional[List[str]] = None,
        output_dir: str = "recordings"
    ):
        """
        Start recording audio tracks
        
        Args:
            recording_types: List of recording types to start (INDIVIDUAL, COMPOSITE)
            user_ids: Optional list of specific user IDs to record (None = all users) 
            output_dir: Directory to save recording files
        """
        if not recording_types:
            logger.warning("No recording types specified")
            return
            
        self._output_dir = Path(output_dir)
        self._target_user_ids = user_ids
        
        # Create output directory if it doesn't exist
        os.makedirs(output_dir, exist_ok=True)

        # Start each recording type
        for recording_type in recording_types:
            self._start_recording_type(recording_type, user_ids)
            self._recording_types.add(recording_type)

    
    def stop_recording(
        self,
        recording_types: Optional[List[RecordingType]] = None,
        user_ids: Optional[List[str]] = None
    ):
        """
        Stop recording for specified types and users.
        
        Args:
            recording_types: Optional list of recording types to stop (None = stop all)
            user_ids: Optional list of user IDs to stop recording (None = stop all users)
        """
        with self._recording_lock:
            if not self.is_recording:
                logger.warning("No recording is currently active")
                return
            
            # If no types specified, stop all
            if recording_types is None:
                recording_types = list(self._recording_types)
            
            # Stop each requested recording type
            for recording_type in recording_types:
                if recording_type not in self._recording_types:
                    logger.warning(f"{recording_type.value} recording is not active")
                    continue
                    
                self._stop_recording_type(recording_type, user_ids)
                self._recording_types.discard(recording_type)
            
            # Clear state if no recording is active
            if not self.is_recording:
                self._clear_recording_state()
                logger.info("All recording stopped")
            else:
                types_str = ", ".join([rt.value for rt in recording_types])
                logger.info(f"Stopped recording types: [{types_str}]")
    
    def record_audio_data(self, pcm_data, user_id: str):
        """
        Record incoming audio data for the specified user.
        
        Args:
            pcm_data: Audio data (PcmData object, bytes, or numpy array)
            user_id: ID of the user whose audio this is
        """
        try:
            if not self.is_recording:
                logger.debug(f"Recording not active, ignoring audio from {user_id}")
                return
                
            # Apply user filtering if specified
            if self._target_user_ids and user_id not in self._target_user_ids:
                logger.debug(f"User {user_id} not in target list, ignoring")
                return

            # Convert PCM data to audio bytes for processing
            audio_bytes = self._convert_to_bytes(pcm_data)
            
            # Record for individual if enabled
            # if RecordingType.INDIVIDUAL in self._recording_types:
            #     logger.debug(f"Recording individual track for {user_id}")
            #     self._add_to_individual(user_id, audio_bytes)
                
            # Record for composite if enabled
            if RecordingType.COMPOSITE in self._recording_types:
                self._add_to_composite_with_timestamp(pcm_data, user_id, audio_bytes)
                
        except Exception as e:
            logger.error(f"Error recording audio for user {user_id}: {e}")
    
    def _quantize_timestamp(self, timestamp: float) -> float:
        """
        Quantize timestamp to align with audio frame boundaries.
        
        Args:
            timestamp: Raw timestamp in seconds
            
        Returns:
            Quantized timestamp aligned to frame boundaries
        """
        # Round to nearest frame boundary (e.g., 0.02s for 20ms frames)
        quantized = round(timestamp / self._frame_duration) * self._frame_duration
        return quantized
    
    def _add_to_composite_with_timestamp(self, pcm_data, user_id: str, audio_bytes: bytes):
        """
        Add audio data to composite recording with timestamp synchronization.
        
        Args:
            pcm_data: Original PCM data (potentially with timestamp info)
            user_id: ID of the user
            audio_bytes: Audio data as bytes
        """
        try:
            # Get current absolute time
            current_absolute_time = time.time()
            
            # Extract relative timestamp from PCM data (this will be relative to when user started)
            relative_timestamp = self._extract_timestamp(pcm_data, user_id)
            
            # Record the absolute start time for this user if not already recorded
            if user_id not in self._user_start_times:
                # Quantize the start time to frame boundaries
                quantized_start_time = self._quantize_timestamp(current_absolute_time)
                self._user_start_times[user_id] = quantized_start_time
                logger.info(f"User {user_id} first frame at quantized absolute time {quantized_start_time:.3f}")
            
            # Set reference start time from the very first user/frame
            if self._reference_start_time is None:
                self._reference_start_time = self._user_start_times[user_id]
                logger.info(f"Reference start time set to {self._reference_start_time:.3f} from user {user_id}")
            
            # Calculate user's absolute timestamp: their absolute start time + relative timestamp from PCM
            user_absolute_timestamp = self._user_start_times[user_id] + relative_timestamp
            
            # Calculate offset for this user relative to reference start time
            user_offset = self._user_start_times[user_id] - self._reference_start_time
            adjusted_timestamp = user_absolute_timestamp - self._reference_start_time
            
            # Quantize the final adjusted timestamp to ensure frame alignment
            quantized_adjusted_timestamp = self._quantize_timestamp(adjusted_timestamp)
            
            # Convert audio to numpy samples
            audio_samples = np.frombuffer(audio_bytes, dtype=np.int16).astype(np.float32)
            
            # Add frame to timestamp map using quantized timestamp
            with self._composite_lock:
                frame_data = {
                    'user_id': user_id,
                    'samples': audio_samples,
                    'relative_timestamp': relative_timestamp,
                    'user_absolute_start': self._user_start_times[user_id],
                    'user_offset': user_offset,
                    'raw_adjusted_timestamp': adjusted_timestamp,
                    'quantized_timestamp': quantized_adjusted_timestamp
                }
                self._timestamp_frame_map[quantized_adjusted_timestamp].append(frame_data)
            
            # Process accumulated frames periodically
            self._process_timestamp_frames()
            
        except Exception as e:
            logger.error(f"Error adding audio to composite for user {user_id}: {e}")
    
    def _extract_timestamp(self, pcm_data, user_id: str) -> float:
        """
        Extract relative timestamp from PCM data or generate one.
        
        Args:
            pcm_data: PCM data object
            user_id: User ID for logging
            
        Returns:
            Relative timestamp in seconds (relative to when this user started)
        """
        # Try to extract timestamp from PCM data
        if hasattr(pcm_data, 'pts_seconds') and pcm_data.pts_seconds is not None:
            return float(pcm_data.pts_seconds)
        elif hasattr(pcm_data, 'pts') and hasattr(pcm_data, 'time_base'):
            if pcm_data.pts is not None and pcm_data.time_base is not None:
                return float(pcm_data.pts * pcm_data.time_base)
        
        # Fallback: generate relative timestamp based on frame count for this user
        if not hasattr(self, '_user_frame_counters'):
            self._user_frame_counters = {}
        
        if user_id not in self._user_frame_counters:
            self._user_frame_counters[user_id] = 0
        
        # Assume 20ms frames (standard for WebRTC)
        relative_timestamp = self._user_frame_counters[user_id] * self._frame_duration
        self._user_frame_counters[user_id] += 1
        
        return relative_timestamp
    
    def _process_timestamp_frames(self):
        """
        Process accumulated frames by timestamp, mixing frames at the same timestamp.
        """
        with self._composite_lock:
            if not self._timestamp_frame_map or not self._composite_recording_file:
                return
            
            # Get timestamps that are ready to be processed
            # Process timestamps that are old enough to ensure we have all concurrent frames
            current_absolute_time = time.time()
            current_recording_time = current_absolute_time - self._reference_start_time if self._reference_start_time else 0
            
            # Quantize the current recording time to ensure we're processing complete frames
            quantized_current_time = self._quantize_timestamp(current_recording_time)
            max_timestamp_to_process = quantized_current_time - self._frame_duration  # Wait for at least one frame delay
            
            # Sort timestamps and process in order
            timestamps_to_process = [
                ts for ts in sorted(self._timestamp_frame_map.keys())
                if ts <= max_timestamp_to_process and ts > self._processed_timestamp
            ]
            
            for timestamp in timestamps_to_process:
                frames = self._timestamp_frame_map[timestamp]
                
                if frames:
                    # Mix all frames at this timestamp by averaging
                    mixed_samples = self._mix_frames_by_averaging(frames)
                    
                    # Write mixed samples to composite file
                    if mixed_samples is not None and len(mixed_samples) > 0:
                        int16_samples = np.clip(mixed_samples, -32767, 32767).astype(np.int16)
                        self._composite_recording_file.writeframes(int16_samples.tobytes())
                    
                    # Remove processed timestamp
                    del self._timestamp_frame_map[timestamp]
                    self._processed_timestamp = timestamp
            
            # Clean up old timestamps that might have been missed
            cutoff_timestamp = quantized_current_time - self._max_timestamp_gap
            timestamps_to_remove = [
                ts for ts in self._timestamp_frame_map.keys()
                if ts < cutoff_timestamp
            ]
            for ts in timestamps_to_remove:
                logger.warning(f"Removing stale quantized timestamp {ts:.3f} (too old)")
                del self._timestamp_frame_map[ts]
    
    def _mix_frames_by_averaging(self, frames: List[Dict]) -> Optional[np.ndarray]:
        """
        Mix multiple audio frames by averaging them.
        
        Args:
            frames: List of frame dictionaries containing samples and metadata
            
        Returns:
            Mixed audio samples as numpy array, or None if no valid frames
        """
        if not frames:
            return None
        
        # Determine the target length (use the most common length)
        lengths = [len(frame['samples']) for frame in frames]
        target_length = max(set(lengths), key=lengths.count) if lengths else 0
        
        if target_length == 0:
            return None
            
        # Initialize mixed samples
        mixed_samples = np.zeros(target_length, dtype=np.float32)
        valid_frame_count = 0
        
        for frame in frames:
            samples = frame['samples']
            if len(samples) == 0:
                continue
                
            # Resize samples to target length if needed
            if len(samples) != target_length:
                if len(samples) < target_length:
                    # Pad with zeros
                    padded_samples = np.zeros(target_length, dtype=np.float32)
                    padded_samples[:len(samples)] = samples
                    samples = padded_samples
                else:
                    # Truncate
                    samples = samples[:target_length]
            
            # Add to mix
            mixed_samples += samples
            valid_frame_count += 1
        
        # Average the samples if we have multiple frames
        if valid_frame_count > 1:
            mixed_samples = mixed_samples / valid_frame_count
        
        return mixed_samples if valid_frame_count > 0 else None
    
    def _convert_to_bytes(self, pcm_data) -> bytes:
        """
        Convert various PCM data formats to bytes.
        
        Args:
            pcm_data: Can be bytes, PcmData object, or numpy array
            
        Returns:
            PCM data as bytes
        """
        # If it's already bytes, return as-is
        if isinstance(pcm_data, bytes):
            return pcm_data
        
        # If it's a PcmData object (has samples attribute)
        if hasattr(pcm_data, 'samples'):
            samples = pcm_data.samples
            if isinstance(samples, bytes):
                return samples
            elif isinstance(samples, np.ndarray):
                # Convert numpy array to bytes
                return samples.astype(np.int16).tobytes()
            else:
                raise ValueError(f"Unsupported PcmData.samples type: {type(samples)}")
        
        # If it's a numpy array directly
        if isinstance(pcm_data, np.ndarray):
            return pcm_data.astype(np.int16).tobytes()
        
        # If it's a memoryview, convert to bytes
        if isinstance(pcm_data, memoryview):
            return bytes(pcm_data)
        
        # Try to convert to bytes as fallback
        try:
            return bytes(pcm_data)
        except Exception as e:
            raise ValueError(f"Cannot convert {type(pcm_data)} to bytes: {e}")
    
    def get_recording_status(self) -> dict:
        """Get current recording status and information."""
        with self._recording_lock:
            with self._composite_lock:
                return {
                    "recording_enabled": self.is_recording,
                    "recording_types": [rt.value for rt in self._recording_types],
                    "output_directory": str(self._output_dir),
                    "active_user_recordings": list(self._recording_files.keys()),
                    "target_user_ids": list(self._target_user_ids) if self._target_user_ids else None,
                    "composite_active": RecordingType.COMPOSITE in self._recording_types,
                    "user_start_times": dict(self._user_start_times),
                    "reference_start_time": self._reference_start_time,
                    "processed_timestamp": self._processed_timestamp,
                    "pending_timestamps": len(self._timestamp_frame_map),
                    "pending_timestamp_range": {
                        "min": min(self._timestamp_frame_map.keys()) if self._timestamp_frame_map else None,
                        "max": max(self._timestamp_frame_map.keys()) if self._timestamp_frame_map else None
                    }
                }
    
    def _start_recording_type(self, recording_type: RecordingType, user_ids: Optional[List[str]] = None):
        """Start a specific recording type."""
        if recording_type == RecordingType.COMPOSITE:
            timestamp = int(time.time())
            user_suffix = f"_users_{'_'.join(sorted(user_ids))}" if user_ids else ""
            composite_filename = self._output_dir.joinpath(f"composite_{timestamp}{user_suffix}.wav")
            self._composite_recording_file = wave.open(str(composite_filename), 'wb')
            self._composite_recording_file.setnchannels(self.AUDIO_CHANNELS)
            self._composite_recording_file.setsampwidth(self.AUDIO_SAMPLE_WIDTH)
            self._composite_recording_file.setframerate(self.AUDIO_SAMPLE_RATE)
            
            logger.info(f"Started composite recording: {composite_filename}")

    def _stop_recording_type(self, recording_type: RecordingType, user_ids: Optional[List[str]] = None):
        """Stop a specific recording type."""
        if recording_type == RecordingType.TRACK:
            self._stop_individual_recording(user_ids)
        elif recording_type == RecordingType.COMPOSITE:
            self._stop_composite_recording()
    
    def _stop_individual_recording(self, user_ids: Optional[List[str]] = None):
        """Stop individual user recording for specific users or all users."""
        if user_ids:
            # Stop recording for specific users
            for user_id in user_ids:
                if user_id in self._recording_files:
                    try:
                        self._recording_files[user_id].close()
                        del self._recording_files[user_id]
                        logger.info(f"Stopped individual recording for user: {user_id}")
                    except Exception as e:
                        logger.error(f"Error stopping recording for user {user_id}: {e}")
        else:
            # Stop all individual recording
            for user_id, file_handle in list(self._recording_files.items()):
                try:
                    file_handle.close()
                    logger.info(f"Closed recording file for user: {user_id}")
                except Exception as e:
                    logger.error(f"Error closing recording file for user {user_id}: {e}")
            self._recording_files.clear()
    
    def _stop_composite_recording(self):
        """Stop composite recording."""
        if self._composite_recording_file:
            try:
                # Process any remaining frames before stopping
                self._flush_remaining_frames()
                
                self._composite_recording_file.close()
                logger.info("Closed composite recording file")
            except Exception as e:
                logger.error(f"Error closing composite recording file: {e}")
            finally:
                self._composite_recording_file = None
    
    def _flush_remaining_frames(self):
        """Flush any remaining frames in the timestamp map."""
        with self._composite_lock:
            if not self._timestamp_frame_map or not self._composite_recording_file:
                return
            
            # Process all remaining timestamps in order
            for timestamp in sorted(self._timestamp_frame_map.keys()):
                frames = self._timestamp_frame_map[timestamp]
                
                if frames:
                    mixed_samples = self._mix_frames_by_averaging(frames)
                    
                    if mixed_samples is not None and len(mixed_samples) > 0:
                        int16_samples = np.clip(mixed_samples, -32767, 32767).astype(np.int16)
                        self._composite_recording_file.writeframes(int16_samples.tobytes())

            self._timestamp_frame_map.clear()
    
    def _get_or_create_user_recording_file(self, user_id: str) -> wave.Wave_write:
        """Get or create a recording file for a specific user."""
        if user_id not in self._recording_files:
            timestamp = int(time.time())
            filename = self._output_dir / f"user_{user_id}_{timestamp}.wav"
            file_handle = wave.open(str(filename), 'wb')
            file_handle.setnchannels(self.AUDIO_CHANNELS)
            file_handle.setsampwidth(self.AUDIO_SAMPLE_WIDTH)
            file_handle.setframerate(self.AUDIO_SAMPLE_RATE)
            self._recording_files[user_id] = file_handle
            logger.info(f"Created recording file for user {user_id}: {filename}")
        
        return self._recording_files[user_id]
    
    def _clear_recording_state(self):
        """Clear all recording state."""
        self._target_user_ids = None
        self._user_start_times.clear()
        self._reference_start_time = None
        self._recording_start_time = None
        self._processed_timestamp = 0.0
        
        # Clear frame counters
        if hasattr(self, '_user_frame_counters'):
            self._user_frame_counters.clear()
        
        with self._composite_lock:
            self._timestamp_frame_map.clear()
    
    def cleanup(self):
        with self._recording_lock:
            # Stop all recording
            if self.is_recording:
                self.stop_recording()
            
            # Ensure all individual files are closed
            for user_id, file_handle in list(self._recording_files.items()):
                try:
                    file_handle.close()
                except Exception as e:
                    logger.error(f"Error closing file for user {user_id}: {e}")
            self._recording_files.clear()
            
            # Ensure composite file is closed
            if self._composite_recording_file:
                try:
                    self._composite_recording_file.close()
                except Exception as e:
                    logger.error(f"Error closing composite file: {e}")
                self._composite_recording_file = None
            
            # Clear all state
            self._clear_recording_state()
