import time
import asyncio
import logging

import aiortc
from av import AudioFrame
from av.frame import Frame
import fractions

from getstream.video.rtc.track_util import PcmData

logger = logging.getLogger(__name__)


class AudioStreamTrack(aiortc.mediastreams.MediaStreamTrack):
    """
    Audio stream track that accepts PcmData objects and buffers them as bytes.

    Works with PcmData objects instead of raw bytes, avoiding format conversion issues.
    Internally buffers as bytes for efficient memory usage.

    Usage:
        track = AudioStreamTrack(sample_rate=48000, channels=2)

        # Write PcmData objects (any format, any sample rate, any channels)
        await track.write(pcm_data)

        # The track will automatically resample/convert to the configured format
    """

    kind = "audio"

    def __init__(
        self,
        sample_rate: int = 48000,
        channels: int = 1,
        format: str = "s16",
        audio_buffer_size_ms: int = 30000,  # 30 seconds default
    ):
        """
        Initialize an AudioStreamTrack that accepts PcmData objects.

        Args:
            sample_rate: Target sample rate in Hz (default: 48000)
            channels: Number of channels - 1=mono, 2=stereo (default: 1)
            format: Audio format - "s16" or "f32" (default: "s16")
            audio_buffer_size_ms: Maximum buffer size in milliseconds (default: 30000ms = 30s)
        """
        super().__init__()
        self.sample_rate = sample_rate
        self.channels = channels
        self.format = format
        self.audio_buffer_size_ms = audio_buffer_size_ms

        logger.debug(
            "Initialized AudioStreamTrack",
            extra={
                "sample_rate": sample_rate,
                "channels": channels,
                "format": format,
                "audio_buffer_size_ms": audio_buffer_size_ms,
            },
        )

        # Internal bytearray buffer for audio data
        self._buffer = bytearray()
        self._buffer_lock = asyncio.Lock()

        # Timing for frame pacing
        self._start = None
        self._timestamp = None
        self._last_frame_time = None

        # Calculate bytes per sample based on format
        self._bytes_per_sample = 2 if format == "s16" else 4  # s16=2 bytes, f32=4 bytes
        self._bytes_per_frame = int(
            aiortc.mediastreams.AUDIO_PTIME
            * self.sample_rate
            * self.channels
            * self._bytes_per_sample
        )

    async def write(self, pcm: PcmData):
        """
        Add PcmData to the buffer.

        The PcmData will be automatically resampled/converted to match
        the track's configured sample_rate, channels, and format,
        then converted to bytes and stored in the buffer.

        Args:
            pcm: PcmData object with audio data
        """
        # Normalize the PCM data to target format immediately
        pcm_normalized = self._normalize_pcm(pcm)

        # Convert to bytes
        audio_bytes = pcm_normalized.to_bytes()

        async with self._buffer_lock:
            # Check buffer size before adding
            max_buffer_bytes = int(
                (self.audio_buffer_size_ms / 1000)
                * self.sample_rate
                * self.channels
                * self._bytes_per_sample
            )

            # Add new data to buffer first
            self._buffer.extend(audio_bytes)

            # Check if we exceeded the limit
            if len(self._buffer) > max_buffer_bytes:
                # Calculate how many bytes to drop from the beginning
                bytes_to_drop = len(self._buffer) - max_buffer_bytes
                dropped_ms = (
                    bytes_to_drop
                    / (self.sample_rate * self.channels * self._bytes_per_sample)
                ) * 1000

                logger.debug(
                    "Audio buffer overflow, dropping %.1fms of audio. Buffer max is %dms",
                    dropped_ms,
                    self.audio_buffer_size_ms,
                    extra={
                        "buffer_size_bytes": len(self._buffer),
                        "incoming_bytes": len(audio_bytes),
                        "dropped_bytes": bytes_to_drop,
                    },
                )

                # Drop from the beginning of the buffer to keep latest data
                self._buffer = self._buffer[bytes_to_drop:]

            buffer_duration_ms = (
                len(self._buffer)
                / (self.sample_rate * self.channels * self._bytes_per_sample)
            ) * 1000

        logger.debug(
            "Added audio to buffer",
            extra={
                "pcm_duration_ms": pcm.duration_ms,
                "buffer_duration_ms": buffer_duration_ms,
                "buffer_size_bytes": len(self._buffer),
            },
        )

    async def flush(self) -> None:
        """
        Clear any pending audio from the buffer.
        Playback stops immediately.
        """
        async with self._buffer_lock:
            bytes_cleared = len(self._buffer)
            self._buffer.clear()

        logger.debug("Flushed audio buffer", extra={"cleared_bytes": bytes_cleared})

    async def recv(self) -> Frame:
        """
        Receive the next 20ms audio frame.

        Returns:
            AudioFrame with the configured sample_rate, channels, and format
        """
        if self.readyState != "live":
            raise aiortc.mediastreams.MediaStreamError

        # Calculate samples needed for 20ms frame
        samples_per_frame = int(aiortc.mediastreams.AUDIO_PTIME * self.sample_rate)

        # Initialize timestamp if not already done
        if self._timestamp is None:
            self._start = time.time()
            self._timestamp = 0
            self._last_frame_time = time.time()
        else:
            # Use timestamp-based pacing to avoid drift over time
            # This ensures we stay synchronized with the expected audio rate
            # even if individual frames have slight timing variations
            self._timestamp += samples_per_frame
            start_ts = self._start or time.time()
            wait = start_ts + (self._timestamp / self.sample_rate) - time.time()
            if wait > 0:
                await asyncio.sleep(wait)

            self._last_frame_time = time.time()

        # Get 20ms of audio data from buffer
        async with self._buffer_lock:
            if len(self._buffer) >= self._bytes_per_frame:
                # We have enough data
                audio_bytes = bytes(self._buffer[: self._bytes_per_frame])
                self._buffer = self._buffer[self._bytes_per_frame :]
            elif len(self._buffer) > 0:
                # We have some data but not enough - pad with silence
                audio_bytes = bytes(self._buffer)
                padding_needed = self._bytes_per_frame - len(audio_bytes)
                audio_bytes += bytes(padding_needed)  # Pad with zeros (silence)
                self._buffer.clear()

                logger.debug(
                    "Padded audio frame with silence",
                    extra={
                        "available_bytes": len(audio_bytes) - padding_needed,
                        "required_bytes": self._bytes_per_frame,
                        "padding_bytes": padding_needed,
                    },
                )
            else:
                # No data at all - emit silence
                audio_bytes = bytes(self._bytes_per_frame)

        # Create AudioFrame
        layout = "stereo" if self.channels == 2 else "mono"

        # Convert format name: "s16" -> "s16", "f32" -> "flt"
        if self.format == "s16":
            av_format = "s16"  # Packed int16
        elif self.format == "f32":
            av_format = "flt"  # Packed float32
        else:
            av_format = "s16"  # Default to s16

        frame = AudioFrame(format=av_format, layout=layout, samples=samples_per_frame)

        # Fill frame with data
        frame.planes[0].update(audio_bytes)

        # Set frame properties
        frame.pts = self._timestamp
        frame.sample_rate = self.sample_rate
        frame.time_base = fractions.Fraction(1, self.sample_rate)

        return frame

    def _normalize_pcm(self, pcm: PcmData) -> PcmData:
        """
        Normalize PcmData to match the track's target format.

        Args:
            pcm: Input PcmData

        Returns:
            PcmData resampled/converted to target sample_rate, channels, and format
        """

        pcm = pcm.resample(self.sample_rate, target_channels=self.channels)

        # Convert format if needed
        if self.format == "s16" and pcm.format != "s16":
            pcm = pcm.to_int16()
        elif self.format == "f32" and pcm.format != "f32":
            pcm = pcm.to_float32()

        return pcm
