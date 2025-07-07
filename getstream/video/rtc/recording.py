import asyncio
import fractions
import logging
import os
import time
from abc import ABC
from collections import defaultdict
from dataclasses import dataclass
from enum import Enum
from pathlib import Path
from typing import Any, Dict, List, Optional, Set, Union

import numpy as np
from aiortc import MediaStreamTrack
from aiortc.contrib.media import MediaRecorder
from aiortc.mediastreams import AudioFrame as AiortcAudioFrame
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
    max_queue_size: int = 10000
    frame_duration: float = 0.02  # 20ms
    max_gap: float = 2.0  # 2 second
    # Audio-specific config
    audio_sample_rate: int = 48000
    audio_channels: int = 1
    audio_sample_width: int = 2  # 16-bit
    # Video-specific config
    video_width: int = 1280
    video_height: int = 720
    video_fps: int = 30
    video_bitrate: int = 2000000  # 2 Mbps


@dataclass
class Frame(ABC):
    """Base class for all frame types."""

    user_id: str
    timestamp: float
    data: bytes
    metadata: Any = (
        None  # Original source data (PcmData for audio, raw video data, etc.)
    )


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
    """Records a single track using MediaRecorder."""

    def __init__(
        self,
        track_type: TrackType,
        track: Optional[MediaStreamTrack] = None,
        filename: Optional[str] = None,
        recorder_id: Optional[str] = None,
        config: Optional[RecordingConfig] = None,
    ):
        super().__init__()
        self.track_type = track_type
        self._track = track
        self._filename = (
            filename or f"{track_type.value}_recording_{int(time.time() * 1000)}"
        )
        self.recorder_id = (
            recorder_id or f"{track_type.value}_recorder_{int(time.time() * 1000)}"
        )
        self.config = config or RecordingConfig()
        self._recorder: Optional[MediaRecorder] = None
        self._is_recording = False
        self._start_time: Optional[float] = None

    @property
    def is_recording(self) -> bool:
        """Check if recording is active."""
        return self._is_recording

    @property
    def filename(self) -> Optional[str]:
        """Get the current recording filename."""
        return self._filename

    async def start_recording(self):
        """Start recording using track and filename from constructor."""
        if self._is_recording:
            logger.warning(f"TrackRecorder {self.recorder_id} is already recording")
            return

        if not self._track:
            raise ValueError(f"No track provided for recording {self.recorder_id}")

        try:
            # Create output directory
            file_format = "m4a" if self.track_type == TrackType.AUDIO else "mp4"

            # Check if filename already has an extension
            if Path(self._filename).suffix:
                filepath = Path(self.config.output_dir) / self._filename
            else:
                filepath = (
                    Path(self.config.output_dir) / f"{self._filename}.{file_format}"
                )

            os.makedirs(filepath.parent, exist_ok=True)

            # Create MediaRecorder
            self._recorder = MediaRecorder(str(filepath))
            logger.info(
                f"TrackRecorder {self.recorder_id}: Created MediaRecorder for {filepath}"
            )
            self._recorder.addTrack(self._track)
            logger.info(
                f"TrackRecorder {self.recorder_id}: Added track {type(self._track).__name__} to MediaRecorder"
            )

            # Start recording
            await self._recorder.start()
            logger.info(
                f"TrackRecorder {self.recorder_id}: MediaRecorder started successfully"
            )
            self._is_recording = True
            self._start_time = time.time()
            self._filename = str(filepath)

            self.emit(
                "recording_started",
                {
                    "recorder_id": self.recorder_id,
                    "track_type": self.track_type.value,
                    "filename": self._filename,
                    "timestamp": self._start_time,
                },
            )

            logger.info(
                f"Started {self.track_type.value} recording {self.recorder_id}: {self._filename}"
            )
        except Exception as e:
            logger.error(f"Error starting recording for {self.recorder_id}: {e}")
            self.emit(
                "recording_error",
                {
                    "recorder_id": self.recorder_id,
                    "track_type": self.track_type.value,
                    "error_type": "start_error",
                    "message": str(e),
                    "timestamp": time.time(),
                },
            )
            raise

    async def stop_recording(self):
        """Stop recording and close the file."""
        if not self._is_recording:
            return

        try:
            duration = time.time() - self._start_time if self._start_time else 0
            filename = self._filename
            # Stop recording
            if self._recorder:
                await self._recorder.stop()
        except Exception as e:
            logger.error(f"Error stopping recording {self.recorder_id}: {e}")
        finally:
            # Clean up
            self._recorder = None
            self._is_recording = False
            self.emit(
                "recording_stopped",
                {
                    "recorder_id": self.recorder_id,
                    "track_type": self.track_type.value,
                    "filename": filename,
                    "duration": duration,
                    "timestamp": time.time(),
                },
            )

        logger.info(
            f"Stopped {self.track_type.value} recording {self.recorder_id} after {duration:.2f}s"
        )


class MixedAudioStreamTrack(MediaStreamTrack):
    """Custom MediaStreamTrack that mixes multiple audio tracks using the existing recording.py logic."""

    kind = "audio"

    def __init__(self, config: RecordingConfig, user_ids: Optional[Set[str]] = None):
        super().__init__()
        self.config = config
        self.user_ids = user_ids
        self._user_tracks: Dict[str, MediaStreamTrack] = {}
        self._running = True

        # Mixing state (same as CompositeAudioRecorder)
        self._frame_map: Dict[float, List[AudioFrame]] = defaultdict(list)
        self._user_start_times: Dict[str, float] = {}
        self._reference_time: Optional[float] = None
        self._processed_time = 0.0
        self._frame_counters: Dict[str, int] = {}

        # Buffer for mixed frames
        self._mixed_frame_buffer: asyncio.Queue = asyncio.Queue(maxsize=100)
        self._mixing_task: Optional[asyncio.Task] = None

        # Debug counter
        self._recv_call_count = 0

        # Start the mixing task
        self._start_mixing_task()

    def _start_mixing_task(self):
        """Start the background mixing task."""
        if self._mixing_task is None or self._mixing_task.done():
            self._mixing_task = asyncio.create_task(self._mixing_loop())

    async def _mixing_loop(self):
        """Background task that continuously reads from tracks and produces mixed frames."""
        logger.debug("Started mixing loop for MixedAudioStreamTrack")

        while self._running:
            try:
                # Collect frames from all user tracks
                frames_collected = []
                current_time = time.time()

                if not self._user_tracks:
                    await asyncio.sleep(0.01)  # Wait longer if no tracks
                    continue

                for user_id, track in list(self._user_tracks.items()):
                    try:
                        # Try to receive frame with short timeout
                        aiortc_frame = await asyncio.wait_for(
                            track.recv(), timeout=0.001
                        )

                        # Convert aiortc frame to our AudioFrame format
                        audio_bytes = self._aiortc_frame_to_bytes(aiortc_frame)
                        if audio_bytes:
                            frame = AudioFrame(
                                user_id=user_id,
                                data=audio_bytes,
                                timestamp=current_time,
                                metadata=aiortc_frame,
                            )
                            frames_collected.append(frame)

                    except (asyncio.TimeoutError, Exception):
                        # No frame available or error, continue
                        continue

                # Process collected frames using existing mixing logic
                if frames_collected:
                    for frame in frames_collected:
                        mixed_audio = await self._process_frame(frame)
                        if mixed_audio:
                            # Convert mixed audio bytes back to aiortc AudioFrame
                            mixed_frame = self._bytes_to_aiortc_frame(mixed_audio)
                            if mixed_frame:
                                # Add to buffer (non-blocking, drop if full)
                                try:
                                    self._mixed_frame_buffer.put_nowait(mixed_frame)
                                except asyncio.QueueFull:
                                    # Drop oldest frame and add new one
                                    try:
                                        self._mixed_frame_buffer.get_nowait()
                                        self._mixed_frame_buffer.put_nowait(mixed_frame)
                                    except asyncio.QueueEmpty:
                                        pass

                # Small delay to prevent busy waiting
                await asyncio.sleep(0.005)  # 5ms

            except Exception as e:
                if self._running:
                    logger.error(f"Error in mixing loop: {e}")
                    await asyncio.sleep(0.01)

        logger.debug("Mixing loop stopped")

    async def recv(self) -> AiortcAudioFrame:
        """Receive mixed audio frame from buffer."""
        self._recv_call_count += 1

        if not self._running:
            return self._create_silent_frame()

        # Wait for tracks to be available first
        if not self._user_tracks:
            # Wait up to 2 seconds for tracks to be added
            for i in range(20):  # 20 * 0.1s = 2s
                if self._user_tracks:
                    logger.debug(f"Tracks now available after {i * 0.1:.1f}s")
                    break
                await asyncio.sleep(0.1)

            if not self._user_tracks:
                return self._create_silent_frame()

        # For the first few calls after tracks are available, wait longer for mixing to start
        timeout = 3.0 if self._recv_call_count <= 5 else 0.1

        try:
            # Wait for mixed frame with timeout
            mixed_frame = await asyncio.wait_for(
                self._mixed_frame_buffer.get(), timeout=timeout
            )
            return mixed_frame
        except asyncio.TimeoutError:
            # Return silent frame if no mixed audio available
            return self._create_silent_frame()
        except Exception as e:
            logger.error(f"Error in recv(): {e}")
            return self._create_silent_frame()

    def _create_silent_frame(self) -> AiortcAudioFrame:
        """Create a silent audio frame."""
        samples_per_frame = int(
            self.config.audio_sample_rate * self.config.frame_duration
        )
        silent_samples = np.zeros(
            (samples_per_frame, self.config.audio_channels), dtype=np.int16
        )

        return AiortcAudioFrame(
            format="s16",
            layout="mono" if self.config.audio_channels == 1 else "stereo",
            samples=silent_samples,
        )

    def _aiortc_frame_to_bytes(self, aiortc_frame: AiortcAudioFrame) -> Optional[bytes]:
        """Convert aiortc AudioFrame to bytes, handling variable frame sizes."""
        try:
            if hasattr(aiortc_frame, "to_ndarray"):
                samples = aiortc_frame.to_ndarray()

                # Handle different array shapes - flatten to 1D
                if samples.ndim > 1:
                    samples = samples.flatten()

                if samples.dtype != np.int16:
                    samples = samples.astype(np.int16)

                # Preserve full frame to maintain audio quality
                return samples.tobytes()
            else:
                # Fallback: use planes
                return aiortc_frame.planes[0].to_bytes()
        except Exception as e:
            logger.warning(f"Error converting aiortc frame to bytes: {e}")
            return None

    def _bytes_to_aiortc_frame(self, audio_bytes: bytes) -> Optional[AiortcAudioFrame]:
        """Convert bytes back to aiortc AudioFrame with normalized frame size."""
        try:
            # Calculate expected frame size for consistent timing (20ms)
            bytes_per_sample = 2  # 16-bit = 2 bytes per sample
            expected_samples = int(
                self.config.audio_sample_rate * self.config.frame_duration
            )
            expected_bytes = (
                expected_samples * self.config.audio_channels * bytes_per_sample
            )
            layout = "mono" if self.config.audio_channels == 1 else "stereo"

            # Normalize audio data to expected frame size to prevent stretched audio
            normalized_bytes = self._normalize_audio_frame_size(
                audio_bytes, expected_bytes
            )

            # Create AudioFrame with consistent frame size
            frame = AiortcAudioFrame(
                format="s16", layout=layout, samples=expected_samples
            )

            # Update the frame planes with our normalized audio data
            for plane in frame.planes:
                plane.update(normalized_bytes)
                break  # For audio, we typically only have one plane

            # Set additional frame properties
            frame.sample_rate = self.config.audio_sample_rate
            frame.time_base = fractions.Fraction(1, self.config.audio_sample_rate)

            return frame
        except Exception as e:
            logger.warning(f"Error converting bytes to aiortc frame: {e}")
            return None

    def _normalize_audio_frame_size(
        self, audio_bytes: bytes, target_bytes: int
    ) -> bytes:
        """Normalize audio frame size to target duration while preserving quality."""
        if len(audio_bytes) == target_bytes:
            return audio_bytes
        elif len(audio_bytes) > target_bytes:
            # Input frame is longer than target - use resampling
            samples = np.frombuffer(audio_bytes, dtype=np.int16)
            target_samples = target_bytes // 2  # 2 bytes per sample

            if len(samples) > 0:
                # Use linear interpolation to resample to target length
                original_indices = np.linspace(0, len(samples) - 1, len(samples))
                target_indices = np.linspace(0, len(samples) - 1, target_samples)

                # Interpolate samples to new length
                resampled = np.interp(
                    target_indices, original_indices, samples.astype(np.float32)
                )
                resampled_int16 = np.clip(resampled, -32767, 32767).astype(np.int16)

                return resampled_int16.tobytes()
            else:
                return bytes(target_bytes)
        else:
            # Input frame is shorter than target - pad with silence
            padding_bytes = target_bytes - len(audio_bytes)
            return audio_bytes + bytes(padding_bytes)

    def add_track(self, user_id: str, track: MediaStreamTrack) -> None:
        """Add a user track to the mix."""
        self._user_tracks[user_id] = track
        logger.info(
            f"Added user {user_id} track. Total tracks: {len(self._user_tracks)}"
        )

        # Signal that tracks are now available for mixing
        if len(self._user_tracks) == 1:
            logger.debug("First track added - mixing can now begin")

    def remove_track(self, user_id: str) -> None:
        """Remove a user track from the mix."""
        if user_id in self._user_tracks:
            del self._user_tracks[user_id]
            # Clean up related state
            if user_id in self._user_start_times:
                del self._user_start_times[user_id]
            if user_id in self._frame_counters:
                del self._frame_counters[user_id]
            logger.info(f"Removed user {user_id} track from mixed audio track")

    def has_tracks(self) -> bool:
        """Check if there are any tracks in the mix."""
        return len(self._user_tracks) > 0

    def stop(self) -> None:
        """Stop the mixed track."""
        self._running = False
        if self._mixing_task and not self._mixing_task.done():
            self._mixing_task.cancel()

    # Mixing logic methods (copied from CompositeAudioRecorder)
    async def _process_frame(self, frame: AudioFrame) -> Optional[bytes]:
        """Process composite frame with timestamp synchronization and mixing."""
        # Apply user filtering
        if self.user_ids and frame.user_id not in self.user_ids:
            return None

        # Extract timestamp
        relative_timestamp = self._extract_timestamp(frame)

        # Update user timing
        if frame.user_id not in self._user_start_times:
            quantized_time = self._quantize_time(frame.timestamp)
            self._user_start_times[frame.user_id] = quantized_time
            logger.info(f"User {frame.user_id} started at {quantized_time:.3f}")

        if self._reference_time is None:
            self._reference_time = self._user_start_times[frame.user_id]
            logger.info(f"Reference time set to {self._reference_time:.3f}")

        # Calculate adjusted timestamp
        user_absolute_time = self._user_start_times[frame.user_id] + relative_timestamp
        adjusted_time = user_absolute_time - self._reference_time
        quantized_time = self._quantize_time(adjusted_time)

        # Store frame in map
        frame.timestamp = quantized_time  # Update frame timestamp
        self._frame_map[quantized_time].append(frame)

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
            ts
            for ts in sorted(self._frame_map.keys())
            if ts <= max_process_time and ts > self._processed_time
        ]

        if not timestamps:
            return None

        # Process the earliest timestamp
        timestamp = timestamps[0]
        frames = self._frame_map[timestamp]

        if frames:
            # Mix frames (using exact same logic)
            mixed_audio = self._mix_frames(frames)
            del self._frame_map[timestamp]
            self._processed_time = timestamp

            # Clean old timestamps
            cutoff = quantized_current - self.config.max_gap
            old_timestamps = [ts for ts in self._frame_map.keys() if ts < cutoff]
            for ts in old_timestamps:
                del self._frame_map[ts]

            return mixed_audio

        return None

    def _mix_frames(self, frames: List[AudioFrame]) -> Optional[bytes]:
        """Mix multiple audio frames by proper audio mixing (addition with clipping)."""
        if not frames:
            return None

        # For single frame, return as-is to avoid unnecessary processing
        if len(frames) == 1:
            return frames[0].data

        # Convert audio data to samples - use int32 to prevent overflow during mixing
        all_samples = []
        for frame in frames:
            try:
                # Keep as int16 initially, then convert to int32 for mixing
                samples = np.frombuffer(frame.data, dtype=np.int16).astype(np.int32)
                all_samples.append(samples)
            except Exception as e:
                logger.warning(f"Error converting frame audio data: {e}")
                continue

        if not all_samples:
            return None

        # Find common length
        lengths = [samples.shape[0] for samples in all_samples]
        target_length = max(set(lengths), key=lengths.count) if lengths else 0

        if target_length == 0:
            return None

        # Use int32 to prevent overflow during addition
        mixed_samples = np.zeros(target_length, dtype=np.int32)
        valid_count = 0

        for i, samples in enumerate(all_samples):
            try:
                if samples.shape[0] == 0:
                    continue

                # Resize if needed
                if samples.shape[0] != target_length:
                    if samples.shape[0] < target_length:
                        padded = np.zeros(target_length, dtype=np.int32)
                        padded[: samples.shape[0]] = samples
                        samples = padded
                    else:
                        samples = samples[:target_length]

                # ADD the samples (proper audio mixing)
                mixed_samples += samples
                valid_count += 1
            except Exception as e:
                logger.warning(f"Error processing sample {i} in _mix_frames: {e}")
                continue

        if valid_count > 0:
            # Use averaging instead of volume scaling to prevent clipping
            if valid_count > 1:
                # Average the mixed samples by dividing by the number of valid tracks
                mixed_samples = (mixed_samples / valid_count).astype(np.int32)
                logger.debug(f"Averaged audio from {valid_count} tracks")

            # Clip to int16 range and convert back
            int16_samples = np.clip(mixed_samples, -32767, 32767).astype(np.int16)
            return int16_samples.tobytes()

        return None

    def _quantize_time(self, timestamp: float) -> float:
        """Quantize timestamp to frame boundaries."""
        return (
            round(timestamp / self.config.frame_duration) * self.config.frame_duration
        )

    def _extract_timestamp(self, frame: AudioFrame) -> float:
        """Extract or generate relative timestamp."""
        # Try to extract from metadata
        if frame.metadata:
            if (
                hasattr(frame.metadata, "pts_seconds")
                and frame.metadata.pts_seconds is not None
            ):
                return float(frame.metadata.pts_seconds)
            elif hasattr(frame.metadata, "pts") and hasattr(
                frame.metadata, "time_base"
            ):
                if (
                    frame.metadata.pts is not None
                    and frame.metadata.time_base is not None
                ):
                    return float(frame.metadata.pts * frame.metadata.time_base)

        # Fallback: use frame counter
        if frame.user_id not in self._frame_counters:
            self._frame_counters[frame.user_id] = 0

        timestamp = self._frame_counters[frame.user_id] * self.config.frame_duration
        self._frame_counters[frame.user_id] += 1

        return timestamp


class CompositeAudioRecorder(TrackRecorder):
    """Records mixed audio from multiple tracks using MixedAudioStreamTrack."""

    def __init__(
        self,
        user_ids: Optional[Set[str]] = None,
        filename: Optional[str] = None,
        config: Optional[RecordingConfig] = None,
    ):
        super().__init__(
            TrackType.AUDIO,
            None,
            filename or "composite_audio",
            "composite_audio",
            config,
        )
        self.user_ids = user_ids
        self._mixed_track: Optional[MixedAudioStreamTrack] = None

    @property
    def frame_count(self) -> int:
        """Get frame count (placeholder for compatibility)."""
        return 0  # MixedAudioStreamTrack doesn't expose this

    async def start_recording(self) -> None:
        """Start composite recording using MixedAudioStreamTrack."""
        if self.is_recording:
            logger.warning("Composite recording is already active")
            return

        # Create mixed audio track
        self._mixed_track = MixedAudioStreamTrack(self.config, self.user_ids)

        # Set the track in parent class
        self._track = self._mixed_track

        # Start recording the mixed track using parent class
        await super().start_recording()

        logger.info(f"Started composite audio recording: {self._filename}")

    async def stop_recording(self) -> None:
        """Stop composite recording."""
        if not self.is_recording:
            return

        # Stop the track recording
        await super().stop_recording()

        # Clean up mixed track
        if self._mixed_track:
            self._mixed_track.stop()
            self._mixed_track = None

        logger.info("Stopped composite audio recording")

    def add_user_track(self, user_id: str, track: MediaStreamTrack):
        """Add a user track to the composite mix."""
        if self._mixed_track:
            self._mixed_track.add_track(user_id, track)

    def remove_user_track(self, user_id: str):
        """Remove a user track from the composite mix."""
        if self._mixed_track:
            self._mixed_track.remove_track(user_id)

    def has_tracks(self) -> bool:
        """Check if there are any tracks in the mix."""
        return self._mixed_track.has_tracks() if self._mixed_track else False


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

        # Tracks that were received before recording started.
        # Mapping of track_id -> (user_id, track)
        self._pending_tracks: Dict[str, tuple[str, MediaStreamTrack]] = {}

        # Recording state
        self._recording_types: Set[RecordingType] = set()
        self._target_user_ids: Optional[Set[str]] = None

        # Track recorders organized by track type
        self._audio_recorders: Dict[str, TrackRecorder] = {}
        self._video_recorders: Dict[str, TrackRecorder] = {}
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
        output_dir: Optional[str] = None,
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

        # Process any tracks that were received before recording was enabled.
        await self._process_pending_tracks()

        self.emit(
            "recording_started",
            {
                "recording_types": [rt.value for rt in recording_types],
                "user_ids": user_ids,
                "output_dir": self.config.output_dir,
                "timestamp": self._recording_start_time,
            },
        )

        logger.info(f"Started recording: {[rt.value for rt in recording_types]}")

    async def stop_recording(
        self,
        recording_types: Optional[List[RecordingType]] = None,
        user_ids: Optional[List[str]] = None,
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
            duration = (
                time.time() - self._recording_start_time
                if self._recording_start_time
                else 0
            )

            self.emit(
                "recording_stopped",
                {
                    "recording_types": [rt.value for rt in recording_types],
                    "user_ids": user_ids,
                    "duration": duration,
                    "timestamp": time.time(),
                },
            )

            logger.info("All recording stopped")

    async def on_user_left(self, user_id: str):
        """Handle user leaving the call."""
        # Remove from composite recorder if it exists
        if self._composite_audio_recorder:
            self._composite_audio_recorder.remove_user_track(user_id)

        # Remove from pending tracks
        for track_id in list(self._pending_tracks.keys()):
            pending_user, _ = self._pending_tracks[track_id]
            if pending_user == user_id:
                del self._pending_tracks[track_id]

        # Stop track recording (both audio and video)
        await self._stop_user_recording(user_id)
        logger.info(f"Stopped recording for user {user_id} who left the call")

    async def on_track_removed(self, user_id: str, track_type: str):
        """Handle track removal."""
        if track_type in ["audio", "video"]:
            recorder_key = f"{user_id}_{track_type}"
            await self._stop_user_recording_by_key(recorder_key, track_type)
            logger.info(
                f"Stopped {track_type} recording for user {user_id} whose {track_type} track was removed"
            )

            # Remove from pending
            for track_id in list(self._pending_tracks.keys()):
                pending_user, pending_track = self._pending_tracks[track_id]
                if pending_user == user_id and pending_track.kind == track_type:
                    del self._pending_tracks[track_id]

    async def on_track_received(self, track, user):
        """Handle new track received from track event."""
        if not track or track.kind not in ["audio", "video"]:
            return

        user_id = getattr(
            user, "user_id", getattr(user, "id", str(user) if user else "unknown_user")
        )

        # Apply user filtering
        if self._target_user_ids and user_id not in self._target_user_ids:
            return

        logger.info(f"Processing {track.kind} track for user {user_id}")

        # Handle audio tracks
        if track.kind == "audio":
            # Add to composite recorder if it exists
            if self._composite_audio_recorder:
                self._composite_audio_recorder.add_user_track(user_id, track)

        # Start track recording if enabled (both audio and video)
        if RecordingType.TRACK in self._recording_types:
            await self._start_user_track_recording(user_id, track)

        # Cache track so that we can start recording later if recording is not
        # yet enabled.
        if RecordingType.TRACK not in self._recording_types:
            self._pending_tracks[track.id] = (user_id, track)

    async def _start_user_track_recording(self, user_id: str, track: MediaStreamTrack):
        """Start recording a user track using MediaRecorder."""
        track_type = TrackType.AUDIO if track.kind == "audio" else TrackType.VIDEO
        recorders_dict = (
            self._audio_recorders if track.kind == "audio" else self._video_recorders
        )

        # Check if user already has this type of track recording
        recorder_key = f"{user_id}_{track.kind}"
        if recorder_key in recorders_dict and recorders_dict[recorder_key].is_recording:
            logger.debug(f"User {user_id} {track.kind} recording already active")
            return

        try:
            timestamp = int(time.time())
            filename = f"user_{user_id}_{track.kind}_{timestamp}"

            # Create track recorder with track and filename
            track_recorder = TrackRecorder(
                track_type, track, filename, f"user_{user_id}_{track.kind}", self.config
            )

            # Forward events
            @track_recorder.on("recording_started")
            def on_recording_started(data):
                self.emit(
                    "user_recording_started",
                    {
                        "user_id": user_id,
                        "track_type": data["track_type"],
                        "filename": data["filename"],
                        "timestamp": data["timestamp"],
                    },
                )

            @track_recorder.on("recording_stopped")
            def on_recording_stopped(data):
                self.emit(
                    "user_recording_stopped",
                    {
                        "user_id": user_id,
                        "track_type": data["track_type"],
                        "filename": data["filename"],
                        "duration": data["duration"],
                        "timestamp": data["timestamp"],
                    },
                )

            @track_recorder.on("recording_error")
            def on_recording_error(data):
                self.emit(
                    "recording_error",
                    {
                        "error_type": data["error_type"],
                        "user_id": user_id,
                        "track_type": data["track_type"],
                        "message": data["message"],
                    },
                )

            # Start recording (track and filename already provided in constructor)
            await track_recorder.start_recording()
            recorders_dict[recorder_key] = track_recorder

        except Exception as e:
            logger.error(
                f"Failed to start {track.kind} recording for user {user_id}: {e}"
            )
            self.emit(
                "recording_error",
                {
                    "error_type": "start_user_recording",
                    "user_id": user_id,
                    "track_type": track.kind,
                    "message": str(e),
                },
            )

    async def _start_recording_type(self, recording_type: RecordingType) -> None:
        """Start a specific recording type."""
        if recording_type == RecordingType.COMPOSITE:
            # Generate filename
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

            filename = f"composite_audio_{timestamp}{user_suffix}"

            # Create composite recorder with filename
            self._composite_audio_recorder = CompositeAudioRecorder(
                self._target_user_ids, filename, self.config
            )
            self._setup_composite_recorder_events()

            # Start composite recording
            await self._composite_audio_recorder.start_recording()

    async def _stop_recording_type(
        self, recording_type: RecordingType, user_ids: Optional[List[str]] = None
    ):
        """Stop a specific recording type."""
        if recording_type == RecordingType.TRACK:
            if user_ids:
                for user_id in user_ids:
                    await self._stop_user_recording(user_id)
            else:
                # Stop all user recordings (both audio and video)
                for recorder_key in list(self._audio_recorders.keys()):
                    await self._stop_user_recording_by_key(recorder_key, "audio")
                for recorder_key in list(self._video_recorders.keys()):
                    await self._stop_user_recording_by_key(recorder_key, "video")

        elif (
            recording_type == RecordingType.COMPOSITE and self._composite_audio_recorder
        ):
            await self._composite_audio_recorder.stop_recording()
            self._composite_audio_recorder = None

    async def _stop_user_recording(self, user_id: str):
        """Stop all recordings for a specific user (both audio and video)."""
        # Stop audio recording
        audio_key = f"{user_id}_audio"
        if audio_key in self._audio_recorders:
            await self._stop_user_recording_by_key(audio_key, "audio")

        # Stop video recording
        video_key = f"{user_id}_video"
        if video_key in self._video_recorders:
            await self._stop_user_recording_by_key(video_key, "video")

    async def _stop_user_recording_by_key(self, recorder_key: str, track_type: str):
        """Stop recording for a specific recorder key."""
        recorders_dict = (
            self._audio_recorders if track_type == "audio" else self._video_recorders
        )

        if recorder_key in recorders_dict:
            recorder = recorders_dict[recorder_key]
            await recorder.stop_recording()
            del recorders_dict[recorder_key]

    def _setup_recorder_events(self):
        """Set up event forwarding for all current recorders."""
        # Set up events for existing audio recorders
        for user_id, recorder in self._audio_recorders.items():
            self._setup_audio_recorder_events(recorder, user_id)

        # Set up events for composite recorder
        if self._composite_audio_recorder:
            self._setup_composite_recorder_events()

    def _create_event_forwarder(
        self, source_event: str, target_event: str, transform_data=None
    ):
        """Create a generic event forwarder function."""

        def forwarder(data):
            if transform_data:
                data = transform_data(data)
            self.emit(target_event, data)

        return forwarder

    def _setup_audio_recorder_events(self, recorder: TrackRecorder, user_id: str):
        """Set up event forwarding for an audio recorder."""

        # Transform function to add user_id to the event data
        def add_user_id(data):
            return {
                "user_id": user_id,
                "track_type": data["track_type"],
                "filename": data["filename"],
                "timestamp": data["timestamp"],
                **(
                    {
                        k: v
                        for k, v in data.items()
                        if k not in ["track_type", "filename", "timestamp"]
                    }
                ),
            }

        def add_user_id_error(data):
            return {
                "error_type": data["error_type"],
                "user_id": user_id,
                "track_type": data["track_type"],
                "message": data["message"],
            }

        recorder.on(
            "recording_started",
            self._create_event_forwarder(
                "recording_started", "user_recording_started", add_user_id
            ),
        )
        recorder.on(
            "recording_stopped",
            self._create_event_forwarder(
                "recording_stopped", "user_recording_stopped", add_user_id
            ),
        )
        recorder.on(
            "recording_error",
            self._create_event_forwarder(
                "recording_error", "recording_error", add_user_id_error
            ),
        )

    def _setup_composite_recorder_events(self):
        """Set up event forwarding for the composite recorder."""
        if not self._composite_audio_recorder:
            return

        # Transform function for composite events
        def add_composite_context(data):
            return {
                "track_type": data["track_type"],
                "filename": data["filename"],
                "timestamp": data["timestamp"],
                **(
                    {
                        k: v
                        for k, v in data.items()
                        if k not in ["track_type", "filename", "timestamp"]
                    }
                ),
            }

        def add_composite_error_context(data):
            return {
                "error_type": data["error_type"],
                "user_id": "composite",
                "track_type": data["track_type"],
                "message": data["message"],
            }

        self._composite_audio_recorder.on(
            "recording_started",
            self._create_event_forwarder(
                "recording_started",
                "composite_recording_started",
                add_composite_context,
            ),
        )
        self._composite_audio_recorder.on(
            "recording_stopped",
            self._create_event_forwarder(
                "recording_stopped",
                "composite_recording_stopped",
                add_composite_context,
            ),
        )
        self._composite_audio_recorder.on(
            "recording_error",
            self._create_event_forwarder(
                "recording_error", "recording_error", add_composite_error_context
            ),
        )

    def _to_bytes(self, pcm_data) -> bytes:
        """Convert PCM data to bytes."""
        if isinstance(pcm_data, bytes):
            return pcm_data

        if hasattr(pcm_data, "samples"):
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
        # Combine audio and video recorder keys
        all_active_recordings = list(self._audio_recorders.keys()) + list(
            self._video_recorders.keys()
        )

        return {
            "recording_enabled": self.is_recording,
            "recording_types": [rt.value for rt in self._recording_types],
            "output_directory": str(self.config.output_dir),
            "active_user_recordings": all_active_recordings,
            "target_user_ids": list(self._target_user_ids)
            if self._target_user_ids
            else None,
            "composite_active": RecordingType.COMPOSITE in self._recording_types,
            "individual_audio_recorders": {
                recorder_key: {
                    "filename": recorder.filename,
                    "frame_count": 0,  # TrackRecorder doesn't track frame count
                    "is_recording": recorder.is_recording,
                    "track_type": recorder.track_type.value,
                }
                for recorder_key, recorder in self._audio_recorders.items()
            },
            "individual_video_recorders": {
                recorder_key: {
                    "filename": recorder.filename,
                    "frame_count": 0,  # TrackRecorder doesn't track frame count
                    "is_recording": recorder.is_recording,
                    "track_type": recorder.track_type.value,
                }
                for recorder_key, recorder in self._video_recorders.items()
            },
            "composite_audio_recorder": {
                "filename": self._composite_audio_recorder.filename
                if self._composite_audio_recorder
                else None,
                "frame_count": self._composite_audio_recorder.frame_count
                if self._composite_audio_recorder
                else 0,
                "is_recording": self._composite_audio_recorder.is_recording
                if self._composite_audio_recorder
                else False,
                "track_type": "audio",
            }
            if self._composite_audio_recorder
            else None,
            "config": {
                "max_queue_size": self.config.max_queue_size,
                "frame_duration": self.config.frame_duration,
                "audio_sample_rate": self.config.audio_sample_rate,
                "video_width": self.config.video_width,
                "video_height": self.config.video_height,
                "video_fps": self.config.video_fps,
                "video_bitrate": self.config.video_bitrate,
            },
        }

    def record_audio_data(self, pcm_data, user_id: str):
        """
        Legacy method for recording audio data directly.
        This is a no-op since the current implementation uses track-based recording.
        """
        logger.debug(
            f"record_audio_data called for user {user_id} - this is a legacy method and will be ignored"
        )
        pass

    async def cleanup(self):
        """Clean up all resources."""
        # Stop all recording
        if self.is_recording:
            await self.stop_recording()

        # Clean up all recorders
        for recorder in self._audio_recorders.values():
            if hasattr(recorder, "stop_recording"):
                await recorder.stop_recording()
        self._audio_recorders.clear()

        for recorder in self._video_recorders.values():
            if hasattr(recorder, "stop_recording"):
                await recorder.stop_recording()
        self._video_recorders.clear()

        if self._composite_audio_recorder:
            await self._composite_audio_recorder.stop_recording()
            self._composite_audio_recorder = None

        logger.info("RecordingManager cleanup completed")

    async def _process_pending_tracks(self):
        """Start recording for any tracks that were received before recording was enabled."""
        if not self._pending_tracks:
            return

        for track_id, (user_id, track) in list(self._pending_tracks.items()):
            try:
                # Filter by requested user_ids if provided
                if self._target_user_ids and user_id not in self._target_user_ids:
                    continue

                # Start individual track recording if requested
                if RecordingType.TRACK in self._recording_types:
                    await self._start_user_track_recording(user_id, track)

                # Add to composite recorder if requested and audio track
                if (
                    RecordingType.COMPOSITE in self._recording_types
                    and track.kind == "audio"
                    and self._composite_audio_recorder is not None
                ):
                    self._composite_audio_recorder.add_user_track(user_id, track)

                # Remove from pending once handled
                del self._pending_tracks[track_id]
            except Exception as e:
                logger.warning(f"Error processing pending track {track_id}: {e}")
