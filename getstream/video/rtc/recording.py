"""
Audio and Video recorder

This module provides recording capabilities with:
- Individual user recording (separate files per user) 
- Composite recording (mixed audio of all users)
- Support for audio and video tracks (video implementation pending)
"""

import asyncio
import logging
import time
import wave
from abc import ABC, abstractmethod
from collections import defaultdict
from dataclasses import dataclass
from enum import Enum
from pathlib import Path
from typing import Dict, List, Optional, Set, Union, Any
import os

import numpy as np
from pyee.asyncio import AsyncIOEventEmitter

logger = logging.getLogger(__name__)


class RecordingType(Enum):
    TRACK = "track"
    COMPOSITE = "composite"


class TrackType(Enum):
    AUDIO = "audio"
    VIDEO = "video"


@dataclass
class RecordingConfig:
    """Configuration for recording."""
    output_dir: str = "recordings"
    max_queue_size: int = 1000
    frame_duration: float = 0.02  # 20ms
    max_gap: float = 1.0  # 1 second
    # Audio-specific config
    audio_sample_rate: int = 48000
    audio_channels: int = 1
    audio_sample_width: int = 2  # 16-bit


@dataclass
class Frame(ABC):
    """Base class for all frame types."""
    user_id: str
    timestamp: float
    data: bytes
    metadata: Any = None  # Original source data (PcmData for audio, raw video data, etc.)


@dataclass
class AudioFrame(Frame):
    """Represents an audio frame with metadata."""
    
    def __post_init__(self):
        # Validate that this is audio data
        if not isinstance(self.data, bytes):
            raise ValueError("AudioFrame data must be bytes")


@dataclass
class VideoFrame(Frame):
    """Represents a video frame with metadata."""
    width: int = 0
    height: int = 0
    format: str = "unknown"


# Union type for all supported frame types
FrameType = Union[AudioFrame, VideoFrame]


class TrackRecorder(AsyncIOEventEmitter):
    """
    Base class for track recording with async frame processing.
    
    Events emitted:
    - recording_started: {recorder_id, track_type, filename, timestamp}
    - recording_stopped: {recorder_id, track_type, filename, duration, timestamp}
    - recording_error: {recorder_id, track_type, error_type, message}
    - frame_processed: {recorder_id, track_type, frame_count, timestamp}
    """
    
    FRAME_WORKER_TIMEOUT = 1.0  # Configurable timeout for frame worker
    
    def __init__(self, recorder_id: str, track_type: TrackType, config: RecordingConfig):
        super().__init__()
        self.recorder_id = recorder_id
        self.track_type = track_type
        self.config = config
        
        # Recording state
        self._is_recording = False
        self._start_time: Optional[float] = None
        self._frame_count = 0
        
        self._frame_queue: Optional[asyncio.Queue] = None
        self._writer_task: Optional[asyncio.Task] = None
        self._running = False
        
        self._file_handle: Optional[Any] = None  # Can be wave.Wave_write or video file handle
        self._filename: Optional[str] = None
        
        # Validate track type support
        if track_type == TrackType.VIDEO:
            raise NotImplementedError("Video recording is not yet implemented")
    
    @property
    def is_recording(self) -> bool:
        """Check if recording is active."""
        return self._is_recording
    
    @property
    def filename(self) -> Optional[str]:
        """Get the current recording filename."""
        return self._filename
    
    @property
    def frame_count(self) -> int:
        """Get the number of frames processed."""
        return self._frame_count
    
    def _get_file_extension(self) -> str:
        """Get the appropriate file extension for the track type."""
        if self.track_type == TrackType.AUDIO:
            return ".wav"
        if self.track_type == TrackType.VIDEO:
            return ".mp4"
        raise ValueError(f"Unsupported track type: {self.track_type}")
    
    def _create_file_handle(self, filepath: Path):
        """Create the appropriate file handle for the track type."""
        if self.track_type == TrackType.AUDIO:
            file_handle = wave.open(str(filepath), 'wb')
            file_handle.setnchannels(self.config.audio_channels)
            file_handle.setsampwidth(self.config.audio_sample_width)
            file_handle.setframerate(self.config.audio_sample_rate)
            return file_handle
        if self.track_type == TrackType.VIDEO:
            raise NotImplementedError("Video file creation not yet implemented")
        raise ValueError(f"Unsupported track type: {self.track_type}")
    
    def _write_to_file(self, data: bytes):
        """Write data to the file (runs in thread pool)."""
        if not self._file_handle:
            return
            
        if self.track_type == TrackType.AUDIO:
            self._file_handle.writeframes(data)
        elif self.track_type == TrackType.VIDEO:
            raise NotImplementedError("Video writing not yet implemented")
    
    async def start_recording(self, base_filename: str):
        """Start recording to the specified file."""
        if self._is_recording:
            logger.warning(f"Recorder {self.recorder_id} is already recording")
            return
        
        try:
            # Add appropriate extension
            extension = self._get_file_extension()
            if not base_filename.endswith(extension):
                filename = base_filename + extension
            else:
                filename = base_filename
            
            # Create output directory
            filepath = Path(self.config.output_dir) / filename
            os.makedirs(filepath.parent, exist_ok=True)
            
            # Create and configure file handle
            self._file_handle = self._create_file_handle(filepath)
            
            self._filename = str(filepath)
            self._is_recording = True
            self._start_time = time.time()
            self._frame_count = 0
            
            # Start async processing
            await self._start_workers()
            
            self.emit('recording_started', {
                'recorder_id': self.recorder_id,
                'track_type': self.track_type.value,
                'filename': self._filename,
                'timestamp': self._start_time
            })
            
            logger.info(f"Started {self.track_type.value} recording {self.recorder_id}: {self._filename}")
            
        except Exception as e:
            logger.error(f"Error starting recording for {self.recorder_id}: {e}")
            await self._cleanup_file()
            self.emit('recording_error', {
                'recorder_id': self.recorder_id,
                'track_type': self.track_type.value,
                'error_type': 'start_error',
                'message': str(e)
            })
            raise
    
    async def stop_recording(self):
        """Stop recording and close the file."""
        if not self._is_recording:
            return
        
        try:
            # Stop workers
            await self._stop_workers()
            
            # Close file
            duration = time.time() - self._start_time if self._start_time else 0
            filename = self._filename
            
            await self._cleanup_file()
            
            self._is_recording = False
            
            self.emit('recording_stopped', {
                'recorder_id': self.recorder_id,
                'track_type': self.track_type.value,
                'filename': filename,
                'duration': duration,
                'frame_count': self._frame_count,
                'timestamp': time.time()
            })
            
            logger.info(f"Stopped {self.track_type.value} recording {self.recorder_id} after {duration:.2f}s ({self._frame_count} frames)")
            
        except Exception as e:
            logger.error(f"Error stopping recording for {self.recorder_id}: {e}")
            # Ensure cleanup even on error
            try:
                await self._cleanup_file()
                self._is_recording = False
            except Exception as cleanup_error:
                logger.error(f"Error during cleanup for {self.recorder_id}: {cleanup_error}")
            
            self.emit('recording_error', {
                'recorder_id': self.recorder_id,
                'track_type': self.track_type.value,
                'error_type': 'stop_error',
                'message': str(e)
            })
    
    async def queue_frame(self, frame: FrameType):
        """Queue a frame for processing (non-blocking)."""
        if not self._is_recording or not self._frame_queue:
            return
        
        # Validate frame type matches track type
        if self.track_type == TrackType.AUDIO and not isinstance(frame, AudioFrame):
            logger.warning(f"Received non-audio frame for audio recorder {self.recorder_id}")
            return
        if self.track_type == TrackType.VIDEO and not isinstance(frame, VideoFrame):
            logger.warning(f"Received non-video frame for video recorder {self.recorder_id}")
            return
        
        try:
            self._frame_queue.put_nowait(frame)
        except asyncio.QueueFull:
            logger.warning(f"Frame queue full for {self.recorder_id}, dropping frame")
            self.emit('recording_error', {
                'recorder_id': self.recorder_id,
                'track_type': self.track_type.value,
                'error_type': 'queue_full',
                'message': 'Frame queue is full, dropping frames'
            })
    
    @abstractmethod
    async def _process_frame(self, frame: FrameType) -> Optional[bytes]:
        """Process a frame and return data to write to file."""
        pass
    
    async def _frame_worker(self):
        """Worker that processes frames from the queue."""
        while self._running:
            try:
                frame = await asyncio.wait_for(self._frame_queue.get(), timeout=self.FRAME_WORKER_TIMEOUT)
                
                # Process the frame
                processed_data = await self._process_frame(frame)
                
                if processed_data and len(processed_data) > 0:
                    # Write to file in thread pool
                    await asyncio.get_event_loop().run_in_executor(
                        None, self._write_to_file, processed_data
                    )
                    self._frame_count += 1
                    
                    self.emit('frame_processed', {
                        'recorder_id': self.recorder_id,
                        'track_type': self.track_type.value,
                        'frame_count': self._frame_count,
                        'timestamp': time.time()
                    })
                
                self._frame_queue.task_done()
                
            except asyncio.TimeoutError:
                continue
            except Exception as e:
                logger.error(f"Error in frame worker for {self.recorder_id}: {e}")
                self.emit('recording_error', {
                    'recorder_id': self.recorder_id,
                    'track_type': self.track_type.value,
                    'error_type': 'processing_error',
                    'message': str(e)
                })
    
    async def _start_workers(self):
        """Start async frame processing workers."""
        if not self._running:
            self._running = True
            self._frame_queue = asyncio.Queue(maxsize=self.config.max_queue_size)
            self._writer_task = asyncio.create_task(self._frame_worker())
    
    async def _stop_workers(self):
        """Stop async frame processing workers."""
        self._running = False
        
        if self._writer_task and not self._writer_task.done():
            self._writer_task.cancel()
            try:
                await self._writer_task
            except asyncio.CancelledError:
                pass
        
        self._writer_task = None
        self._frame_queue = None
    
    async def _cleanup_file(self):
        """Clean up file handle."""
        if self._file_handle:
            file_handle = self._file_handle
            self._file_handle = None  # Clear reference first
            try:
                # Run file close in thread pool to avoid blocking
                await asyncio.get_event_loop().run_in_executor(
                    None, file_handle.close
                )
            except Exception as e:
                logger.error(f"Error closing file for {self.recorder_id}: {e}")
            finally:
                self._filename = None
    
    async def cleanup(self):
        """Clean up all resources."""
        if self._is_recording:
            await self.stop_recording()
        
        await self._stop_workers()
        await self._cleanup_file()


class AudioTrackRecorder(TrackRecorder):
    """Track recorder for individual user audio tracks."""
    
    def __init__(self, user_id: str, config: RecordingConfig):
        super().__init__(f"user_{user_id}", TrackType.AUDIO, config)
        self.user_id = user_id
    
    async def _process_frame(self, frame: FrameType) -> Optional[bytes]:
        """Process individual audio frame - just pass through the audio data."""
        # Frame type already validated in queue_frame, so we can safely cast
        audio_frame = frame  # type: AudioFrame
            
        if audio_frame.user_id != self.user_id:
            logger.warning(f"Frame user_id {audio_frame.user_id} doesn't match recorder user_id {self.user_id}")
            return None
        
        return audio_frame.data


class CompositeAudioRecorder(TrackRecorder):
    """Track recorder for composite audio with mixing capabilities."""
    
    def __init__(self, config: RecordingConfig, target_user_ids: Optional[Set[str]] = None):
        super().__init__("composite_audio", TrackType.AUDIO, config)
        self.target_user_ids = target_user_ids
        
        # Composite recording state (keeping exact same logic as before)
        self._frame_map: Dict[float, List[AudioFrame]] = defaultdict(list)
        self._user_start_times: Dict[str, float] = {}
        self._reference_time: Optional[float] = None
        self._processed_time = 0.0
        self._frame_counters: Dict[str, int] = {}
    
    async def _process_frame(self, frame: FrameType) -> Optional[bytes]:
        """Process composite frame with timestamp synchronization and mixing."""
        # Frame type already validated in queue_frame, so we can safely cast
        audio_frame = frame  # type: AudioFrame
            
        # Apply user filtering
        if self.target_user_ids and audio_frame.user_id not in self.target_user_ids:
            return None
        
        # Extract timestamp
        relative_timestamp = self._extract_timestamp(audio_frame)
        
        # Update user timing
        if audio_frame.user_id not in self._user_start_times:
            quantized_time = self._quantize_time(audio_frame.timestamp)
            self._user_start_times[audio_frame.user_id] = quantized_time
            logger.info(f"User {audio_frame.user_id} started at {quantized_time:.3f}")
        
        if self._reference_time is None:
            self._reference_time = self._user_start_times[audio_frame.user_id]
            logger.info(f"Reference time set to {self._reference_time:.3f}")
        
        # Calculate adjusted timestamp
        user_absolute_time = self._user_start_times[audio_frame.user_id] + relative_timestamp
        adjusted_time = user_absolute_time - self._reference_time
        quantized_time = self._quantize_time(adjusted_time)
        
        # Store frame in map
        audio_frame.timestamp = quantized_time  # Update frame timestamp
        self._frame_map[quantized_time].append(audio_frame)
        
        # Process ready frames
        return await self._process_ready_frames()
    
    async def _process_ready_frames(self) -> Optional[bytes]:
        """Process and mix ready frames."""
        if not self._reference_time:
            return None
        
        current_time = time.time()
        current_recording_time = current_time - self._reference_time
        quantized_current = self._quantize_time(current_recording_time)
        max_process_time = quantized_current - self.config.frame_duration
        
        # Get timestamps to process
        timestamps = [
            ts for ts in sorted(self._frame_map.keys())
            if ts <= max_process_time and ts > self._processed_time
        ]
        
        if not timestamps:
            return None
        
        # Process the earliest timestamp
        timestamp = timestamps[0]
        frames = self._frame_map[timestamp]
        
        if frames:
            # Mix frames (keeping exact same logic)
            mixed_audio = self._mix_frames(frames)
            del self._frame_map[timestamp]
            self._processed_time = timestamp
            
            # Clean old timestamps
            cutoff = quantized_current - self.config.max_gap
            old_timestamps = [ts for ts in self._frame_map.keys() if ts < cutoff]
            for ts in old_timestamps:
                logger.warning(f"Removing stale timestamp {ts:.3f}")
                del self._frame_map[ts]
            
            return mixed_audio
        
        return None
    
    def _mix_frames(self, frames: List[AudioFrame]) -> Optional[bytes]:
        """Mix multiple audio frames by averaging (EXACT SAME LOGIC)."""
        if not frames:
            return None
        
        # Convert audio data to samples
        all_samples = []
        for frame in frames:
            try:
                samples = np.frombuffer(frame.data, dtype=np.int16).astype(np.float32)
                all_samples.append(samples)
            except Exception as e:
                logger.warning(f"Error converting frame audio data: {e}")
                continue
        
        if not all_samples:
            return None
        
        # Find common length
        lengths = [len(samples) for samples in all_samples]
        target_length = max(set(lengths), key=lengths.count) if lengths else 0
        
        if target_length == 0:
            return None
            
        mixed_samples = np.zeros(target_length, dtype=np.float32)
        valid_count = 0
        
        for samples in all_samples:
            if len(samples) == 0:
                continue
                
            # Resize if needed
            if len(samples) != target_length:
                if len(samples) < target_length:
                    padded = np.zeros(target_length, dtype=np.float32)
                    padded[:len(samples)] = samples
                    samples = padded
                else:
                    samples = samples[:target_length]
            
            mixed_samples += samples
            valid_count += 1
        
        if valid_count > 1:
            mixed_samples = mixed_samples / valid_count
        
        if valid_count > 0:
            int16_samples = np.clip(mixed_samples, -32767, 32767).astype(np.int16)
            return int16_samples.tobytes()
        
        return None
    
    def _quantize_time(self, timestamp: float) -> float:
        """Quantize timestamp to frame boundaries."""
        return round(timestamp / self.config.frame_duration) * self.config.frame_duration
    
    def _extract_timestamp(self, frame: FrameType) -> float:
        """Extract or generate relative timestamp."""
        # Ensure we have an AudioFrame for composite processing
        if not isinstance(frame, AudioFrame):
            return 0.0  # Fallback for non-audio frames
            
        # Try to extract from metadata
        if frame.metadata:
            if hasattr(frame.metadata, 'pts_seconds') and frame.metadata.pts_seconds is not None:
                return float(frame.metadata.pts_seconds)
            elif hasattr(frame.metadata, 'pts') and hasattr(frame.metadata, 'time_base'):
                if frame.metadata.pts is not None and frame.metadata.time_base is not None:
                    return float(frame.metadata.pts * frame.metadata.time_base)
        
        # Fallback: use frame counter
        if frame.user_id not in self._frame_counters:
            self._frame_counters[frame.user_id] = 0
        
        timestamp = self._frame_counters[frame.user_id] * self.config.frame_duration
        self._frame_counters[frame.user_id] += 1
        
        return timestamp
    
    async def cleanup(self):
        """Clean up composite recording state."""
        await super().cleanup()
        self._frame_map.clear()
        self._user_start_times.clear()
        self._reference_time = None
        self._processed_time = 0.0
        self._frame_counters.clear()


class RecordingManager(AsyncIOEventEmitter):
    """
    Manages all audio and video recording operations.
    
    Events emitted:
    - recording_started: {recording_types, user_ids, output_dir}
    - recording_stopped: {recording_types, user_ids, duration}
    - user_recording_started: {user_id, track_type, filename}
    - user_recording_stopped: {user_id, track_type, filename, duration}
    - composite_recording_started: {track_type, filename}
    - composite_recording_stopped: {track_type, filename, duration}
    - recording_error: {error_type, user_id, track_type, message}
    """
    
    def __init__(self, config: Optional[RecordingConfig] = None):
        super().__init__()
        
        self.config = config or RecordingConfig()
        
        # Recording state
        self._recording_types: Set[RecordingType] = set()
        self._target_user_ids: Optional[Set[str]] = None
        
        # Track recorders organized by track type
        self._audio_recorders: Dict[str, AudioTrackRecorder] = {}
        self._composite_audio_recorder: Optional[CompositeAudioRecorder] = None

        self._recording_start_time: Optional[float] = None
    
    @property
    def is_recording(self) -> bool:
        """Check if any recording is currently active."""
        return len(self._recording_types) > 0
    
    @property
    def recording_types(self) -> Set[RecordingType]:
        """Get currently active recording types."""
        return self._recording_types.copy()
    
    async def start_recording(
        self,
        recording_types: List[RecordingType],
        user_ids: Optional[List[str]] = None,
        output_dir: Optional[str] = None
    ):
        """Start recording with specified types and configuration."""
        if not recording_types:
            logger.warning("No recording types specified")
            return
        
        # Update config if output_dir provided
        if output_dir:
            self.config.output_dir = output_dir
        
        self._target_user_ids = set(user_ids) if user_ids else None
        self._recording_start_time = time.time()
        
        # Create output directory
        os.makedirs(self.config.output_dir, exist_ok=True)
        
        # Start recording types
        for recording_type in recording_types:
            await self._start_recording_type(recording_type)
            self._recording_types.add(recording_type)
        
        # Set up event forwarding for new recorders
        self._setup_recorder_events()
        
        self.emit('recording_started', {
            'recording_types': [rt.value for rt in recording_types],
            'user_ids': user_ids,
            'output_dir': self.config.output_dir,
            'timestamp': self._recording_start_time
        })
        
        logger.info(f"Started recording: {[rt.value for rt in recording_types]}")
    
    async def stop_recording(
        self,
        recording_types: Optional[List[RecordingType]] = None,
        user_ids: Optional[List[str]] = None
    ):
        """Stop recording for specified types and users."""
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
                
            await self._stop_recording_type(recording_type, user_ids)
            self._recording_types.discard(recording_type)
        
        # If all recording stopped, emit final event
        if not self.is_recording:
            duration = time.time() - self._recording_start_time if self._recording_start_time else 0
            
            self.emit('recording_stopped', {
                'recording_types': [rt.value for rt in recording_types],
                'user_ids': user_ids,
                'duration': duration,
                'timestamp': time.time()
            })
            
            logger.info("All recording stopped")
    
    def record_audio_data(self, pcm_data, user_id: str):
        """Record incoming audio data"""
        try:
            if not self.is_recording:
                return
                
            if self._target_user_ids and user_id not in self._target_user_ids:
                return

            audio_bytes = self._to_bytes(pcm_data)
            current_time = time.time()
            
            # Create audio frame
            frame = AudioFrame(
                user_id=user_id,
                data=audio_bytes,
                timestamp=current_time,
                metadata=pcm_data
            )
            
            # Queue for individual recording
            if RecordingType.TRACK in self._recording_types:
                recorder = self._get_or_create_audio_recorder(user_id)
                asyncio.create_task(recorder.queue_frame(frame))
                
            # Queue for composite recording
            if RecordingType.COMPOSITE in self._recording_types and self._composite_audio_recorder:
                asyncio.create_task(self._composite_audio_recorder.queue_frame(frame))
                
        except Exception as e:
            logger.error(f"Error queuing audio for user {user_id}: {e}")
            self.emit('recording_error', {
                'error_type': 'queue_error',
                'user_id': user_id,
                'track_type': 'audio',
                'message': str(e)
            })
    
    async def on_user_left(self, user_id: str):
        """Handle user leaving the call."""
        if user_id in self._audio_recorders:
            await self._stop_user_recording(user_id)
            logger.info(f"Stopped recording for user {user_id} who left the call")
    
    async def on_track_removed(self, user_id: str, track_type: str):
        """Handle track removal."""
        if track_type == "audio" and user_id in self._audio_recorders:
            await self._stop_user_recording(user_id)
            logger.info(f"Stopped recording for user {user_id} whose audio track was removed")
    
    def _get_or_create_audio_recorder(self, user_id: str) -> AudioTrackRecorder:
        """Get or create an audio recorder for a user."""
        if user_id not in self._audio_recorders:
            recorder = AudioTrackRecorder(user_id, self.config)
            self._audio_recorders[user_id] = recorder
            
            # Set up event forwarding
            self._setup_audio_recorder_events(recorder, user_id)
            
            # Start recording asynchronously
            timestamp = int(time.time())
            filename = f"user_{user_id}_{timestamp}"  # Extension added automatically
            asyncio.create_task(recorder.start_recording(filename))
        
        return self._audio_recorders[user_id]
    
    async def _start_recording_type(self, recording_type: RecordingType):
        """Start a specific recording type."""
        if recording_type == RecordingType.COMPOSITE:
            self._composite_audio_recorder = CompositeAudioRecorder(self.config, self._target_user_ids)
            self._setup_composite_recorder_events()
            
            # Start composite recording
            timestamp = int(time.time())
            
            # Optimize filename generation for large user lists
            if self._target_user_ids:
                sorted_users = sorted(self._target_user_ids)
                if len(sorted_users) > 5:  # Limit filename length for many users
                    user_suffix = f"_users_{len(sorted_users)}_users"
                else:
                    user_suffix = f"_users_{'_'.join(sorted_users)}"
            else:
                user_suffix = ""
                
            filename = f"composite_audio_{timestamp}{user_suffix}"  # Extension added automatically
            await self._composite_audio_recorder.start_recording(filename)
    
    async def _stop_recording_type(self, recording_type: RecordingType, user_ids: Optional[List[str]] = None):
        """Stop a specific recording type."""
        if recording_type == RecordingType.TRACK:
            if user_ids:
                for user_id in user_ids:
                    await self._stop_user_recording(user_id)
            else:
                # Stop all user recordings
                for user_id in list(self._audio_recorders.keys()):
                    await self._stop_user_recording(user_id)
        
        elif recording_type == RecordingType.COMPOSITE and self._composite_audio_recorder:
            await self._composite_audio_recorder.stop_recording()
            self._composite_audio_recorder = None
    
    async def _stop_user_recording(self, user_id: str):
        """Stop recording for a specific user."""
        if user_id in self._audio_recorders:
            recorder = self._audio_recorders[user_id]
            await recorder.stop_recording()
            del self._audio_recorders[user_id]
    
    def _setup_recorder_events(self):
        """Set up event forwarding for all current recorders."""
        # Set up events for existing audio recorders
        for user_id, recorder in self._audio_recorders.items():
            self._setup_audio_recorder_events(recorder, user_id)
        
        # Set up events for composite recorder
        if self._composite_audio_recorder:
            self._setup_composite_recorder_events()
    
    def _create_event_forwarder(self, source_event: str, target_event: str, transform_data=None):
        """Create a generic event forwarder function."""
        def forwarder(data):
            if transform_data:
                data = transform_data(data)
            self.emit(target_event, data)
        return forwarder
    
    def _setup_audio_recorder_events(self, recorder: AudioTrackRecorder, user_id: str):
        """Set up event forwarding for an audio recorder."""
        # Transform function to add user_id to the event data
        def add_user_id(data):
            return {
                'user_id': user_id,
                'track_type': data['track_type'],
                'filename': data['filename'],
                'timestamp': data['timestamp'],
                **({k: v for k, v in data.items() if k not in ['track_type', 'filename', 'timestamp']})
            }
        
        def add_user_id_error(data):
            return {
                'error_type': data['error_type'],
                'user_id': user_id,
                'track_type': data['track_type'],
                'message': data['message']
            }
        
        recorder.on('recording_started', self._create_event_forwarder(
            'recording_started', 'user_recording_started', add_user_id
        ))
        recorder.on('recording_stopped', self._create_event_forwarder(
            'recording_stopped', 'user_recording_stopped', add_user_id
        ))
        recorder.on('recording_error', self._create_event_forwarder(
            'recording_error', 'recording_error', add_user_id_error
        ))
    
    def _setup_composite_recorder_events(self):
        """Set up event forwarding for the composite recorder."""
        if not self._composite_audio_recorder:
            return
        
        # Transform function for composite events
        def add_composite_context(data):
            return {
                'track_type': data['track_type'],
                'filename': data['filename'],
                'timestamp': data['timestamp'],
                **({k: v for k, v in data.items() if k not in ['track_type', 'filename', 'timestamp']})
            }
        
        def add_composite_error_context(data):
            return {
                'error_type': data['error_type'],
                'user_id': 'composite',
                'track_type': data['track_type'],
                'message': data['message']
            }
        
        self._composite_audio_recorder.on('recording_started', self._create_event_forwarder(
            'recording_started', 'composite_recording_started', add_composite_context
        ))
        self._composite_audio_recorder.on('recording_stopped', self._create_event_forwarder(
            'recording_stopped', 'composite_recording_stopped', add_composite_context
        ))
        self._composite_audio_recorder.on('recording_error', self._create_event_forwarder(
            'recording_error', 'recording_error', add_composite_error_context
        ))
    
    def _to_bytes(self, pcm_data) -> bytes:
        """Convert PCM data to bytes."""
        if isinstance(pcm_data, bytes):
            return pcm_data
        
        if hasattr(pcm_data, 'samples'):
            samples = pcm_data.samples
            if isinstance(samples, bytes):
                return samples
            elif isinstance(samples, np.ndarray):
                return samples.astype(np.int16).tobytes()
            else:
                raise ValueError(f"Unsupported PcmData.samples type: {type(samples)}")
        
        if isinstance(pcm_data, np.ndarray):
            return pcm_data.astype(np.int16).tobytes()
        
        if isinstance(pcm_data, memoryview):
            return bytes(pcm_data)
        
        try:
            return bytes(pcm_data)
        except Exception as e:
            raise ValueError(f"Cannot convert {type(pcm_data)} to bytes: {e}")
    
    def get_recording_status(self) -> dict:
        """Get current recording status."""
        return {
            "recording_enabled": self.is_recording,
            "recording_types": [rt.value for rt in self._recording_types],
            "output_directory": str(self.config.output_dir),
            "active_user_recordings": list(self._audio_recorders.keys()),
            "target_user_ids": list(self._target_user_ids) if self._target_user_ids else None,
            "composite_active": RecordingType.COMPOSITE in self._recording_types,
            "individual_audio_recorders": {
                user_id: {
                    "filename": recorder.filename,
                    "frame_count": recorder.frame_count,
                    "is_recording": recorder.is_recording,
                    "track_type": recorder.track_type.value
                }
                for user_id, recorder in self._audio_recorders.items()
            },
            "composite_audio_recorder": {
                "filename": self._composite_audio_recorder.filename if self._composite_audio_recorder else None,
                "frame_count": self._composite_audio_recorder.frame_count if self._composite_audio_recorder else 0,
                "is_recording": self._composite_audio_recorder.is_recording if self._composite_audio_recorder else False,
                "track_type": "audio"
            } if self._composite_audio_recorder else None,
            "config": {
                "max_queue_size": self.config.max_queue_size,
                "frame_duration": self.config.frame_duration,
                "audio_sample_rate": self.config.audio_sample_rate,
            }
        }
    
    async def cleanup(self):
        """Clean up all resources."""
        # Stop all recording
        if self.is_recording:
            await self.stop_recording()
        
        # Clean up all recorders
        for recorder in self._audio_recorders.values():
            await recorder.cleanup()
        self._audio_recorders.clear()
        
        if self._composite_audio_recorder:
            await self._composite_audio_recorder.cleanup()
            self._composite_audio_recorder = None
        
        logger.info("RecordingManager cleanup completed")

