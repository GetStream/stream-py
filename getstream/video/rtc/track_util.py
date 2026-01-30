import asyncio
import base64
import fractions
import io
import logging
import re
import time
import wave
from enum import Enum
from fractions import Fraction
from typing import (
    Any,
    AsyncIterator,
    Callable,
    Dict,
    Iterator,
    Literal,
    Optional,
    Union,
)

import aiortc
import aiortc.sdp
import av
import numpy as np
from aiortc import MediaStreamTrack
from aiortc.mediastreams import MediaStreamError
from numpy.typing import NDArray

from getstream.video.rtc.g711 import (
    ALAW_DECODE_TABLE,
    MULAW_DECODE_TABLE,
    G711Encoding,
    G711Mapping,
)

logger = logging.getLogger(__name__)


class AudioFormat(str, Enum):
    """
    Audio format constants for PCM data.

    Inherits from str to maintain backward compatibility with string-based APIs.

    Attributes:
        S16: Signed 16-bit integer format (range: -32768 to 32767)
        F32: 32-bit floating point format (range: -1.0 to 1.0)

    Example:
        >>> from getstream.video.rtc.track_util import AudioFormat, PcmData
        >>> import numpy as np
        >>> pcm = PcmData(samples=np.array([1, 2], np.int16), sample_rate=16000, format=AudioFormat.S16)
        >>> pcm.format == AudioFormat.S16
        True
        >>> pcm.format == "s16"  # Can compare with string directly
        True
    """

    S16 = "s16"  # Signed 16-bit integer
    F32 = "f32"  # 32-bit float

    @staticmethod
    def validate(fmt: str) -> str:
        """
        Validate that a format string is one of the supported audio formats.

        Args:
            fmt: Format string to validate

        Returns:
            The validated format string

        Raises:
            ValueError: If format is not supported

        Example:
            >>> AudioFormat.validate("s16")
            's16'
            >>> AudioFormat.validate("invalid")  # doctest: +ELLIPSIS
            Traceback (most recent call last):
                ...
            ValueError: Invalid audio format: 'invalid'. Must be one of: ...
        """
        valid_formats = {f.value for f in AudioFormat}
        if fmt not in valid_formats:
            raise ValueError(
                f"Invalid audio format: {fmt!r}. Must be one of: {', '.join(sorted(valid_formats))}"
            )
        return fmt


# Type alias for audio format parameters
# Accepts both AudioFormat enum members and string literals for backwards compatibility
AudioFormatType = Union[AudioFormat, Literal["s16", "f32"]]

# G.711 encoding constants
MULAW_ENCODE_BIAS = 33
MULAW_MAX = 32635
ALAW_ENCODE_BIAS = 33
ALAW_MAX = 32635


class PcmData:
    """
    A class representing PCM audio data.

    Attributes:
        format: The format of the audio data (use AudioFormat.S16 or AudioFormat.F32)
        sample_rate: The sample rate of the audio data.
        samples: The audio samples as a numpy array.
        pts: The presentation timestamp of the audio data.
        dts: The decode timestamp of the audio data.
        time_base: The time base for converting timestamps to seconds.
        channels: Number of audio channels (1=mono, 2=stereo)
        participant: The participant context for this audio data.
    """

    def __init__(
        self,
        sample_rate: int,
        format: AudioFormatType,
        samples: Optional[NDArray] = None,
        pts: Optional[int] = None,
        dts: Optional[int] = None,
        time_base: Optional[float] = None,
        channels: int = 1,
        participant: Any = None,
    ):
        """
        Initialize PcmData.

        Args:
            sample_rate: The sample rate of the audio data
            format: The format of the audio data (use AudioFormat.S16 or AudioFormat.F32)
            samples: The audio samples as a numpy array (default: empty array with dtype matching format)
            pts: The presentation timestamp of the audio data
            dts: The decode timestamp of the audio data
            time_base: The time base for converting timestamps to seconds
            channels: Number of audio channels (1=mono, 2=stereo)
            participant: The participant context for this audio data

        Raises:
            TypeError: If samples dtype does not match the declared format
        """
        self.format: AudioFormatType = format
        self.sample_rate: int = sample_rate

        # Determine default dtype based on format when samples is None
        if samples is None:
            # Use same pattern as clear() method for consistency
            fmt = (format or "").lower()
            if fmt in ("f32", "float32"):
                dtype = np.float32
            else:
                dtype = np.int16
            samples = np.array([], dtype=dtype)

        # Strict validation: ensure samples dtype matches format
        if isinstance(samples, np.ndarray):
            fmt = (format or "").lower()
            expected_dtype = np.float32 if fmt in ("f32", "float32") else np.int16

            if samples.dtype != expected_dtype:
                # Provide helpful error message with conversion suggestions
                actual_dtype_name = (
                    "float32"
                    if samples.dtype == np.float32
                    else "int16"
                    if samples.dtype == np.int16
                    else str(samples.dtype)
                )
                expected_dtype_name = (
                    "float32" if expected_dtype == np.float32 else "int16"
                )

                raise TypeError(
                    f"Dtype mismatch: format='{format}' requires samples with dtype={expected_dtype_name}, "
                    f"but got dtype={actual_dtype_name}. "
                    f"To fix: use .to_float32() for f32 format, or ensure samples match the declared format. "
                    f"For automatic conversion, use PcmData.from_numpy() instead."
                )

        self.samples: NDArray = samples
        self.pts: Optional[int] = pts
        self.dts: Optional[int] = dts
        self.time_base: Optional[float] = time_base
        self.channels: int = channels
        self.participant: Any = participant

    def __repr__(self) -> str:
        """
        Return a string representation of the PcmData object.

        Returns:
            str: String representation
        """
        return str(self)

    def __str__(self) -> str:
        """
        Return a user-friendly string representation of the PcmData object.

        Returns:
            str: Human-readable description of the audio data
        """
        # Get sample count
        if self.samples.ndim == 2:
            sample_count = (
                self.samples.shape[1]
                if self.samples.shape[0] == self.channels
                else self.samples.shape[0]
            )
        else:
            sample_count = len(self.samples)

        # Get channel description
        if self.channels == 1:
            channel_desc = "Mono"
        elif self.channels == 2:
            channel_desc = "Stereo"
        else:
            channel_desc = f"{self.channels}-channel"

        # Get duration
        duration_s = self.duration
        if duration_s >= 1.0:
            duration_str = f"{duration_s:.2f}s"
        else:
            duration_str = f"{self.duration_ms:.1f}ms"

        # Format description
        format_desc = (
            "16-bit PCM"
            if self.format == "s16"
            else "32-bit float"
            if self.format == "f32"
            else self.format
        )

        return (
            f"{channel_desc} audio: {self.sample_rate}Hz, {format_desc}, "
            f"{sample_count} samples, {duration_str}"
        )

    @property
    def stereo(self) -> bool:
        return self.channels == 2

    @property
    def duration(self) -> float:
        """
        Calculate the duration of the audio data in seconds.

        Returns:
            float: Duration in seconds.
        """
        # The samples field is always a numpy array of audio samples
        # For s16 format, each element in the array is one sample (int16)
        # For f32 format, each element in the array is one sample (float32)

        # If array has shape (channels, samples) or (samples, channels), duration uses the samples dimension
        if self.samples.ndim == 2:
            # Determine which dimension is samples vs channels
            # Standard format is (channels, samples), but we need to handle both
            ch = self.channels if self.channels else 1
            if self.samples.shape[0] == ch:
                # Shape is (channels, samples) - correct format
                num_samples = self.samples.shape[1]
            elif self.samples.shape[1] == ch:
                # Shape is (samples, channels) - transposed format
                num_samples = self.samples.shape[0]
            else:
                # Ambiguous or unknown - assume (channels, samples) and pick larger dimension
                # This handles edge cases like (2, 2) arrays
                num_samples = max(self.samples.shape[0], self.samples.shape[1])
        else:
            num_samples = len(self.samples)

        # Calculate duration based on sample rate
        return num_samples / self.sample_rate

    @property
    def duration_ms(self) -> float:
        """Duration in milliseconds computed from samples and sample rate."""
        return self.duration * 1000.0

    @property
    def pts_seconds(self) -> Optional[float]:
        if self.pts is not None and self.time_base is not None:
            return self.pts * self.time_base
        return None

    @property
    def dts_seconds(self) -> Optional[float]:
        if self.dts is not None and self.time_base is not None:
            return self.dts * self.time_base
        return None

    @classmethod
    def from_bytes(
        cls,
        audio_bytes: bytes,
        sample_rate: int = 16000,
        format: AudioFormatType = AudioFormat.S16,
        channels: int = 1,
    ) -> "PcmData":
        """Build from raw PCM bytes (interleaved).

        Args:
            audio_bytes: Raw PCM audio bytes
            sample_rate: Sample rate in Hz (default: 16000)
            format: Audio format (default: AudioFormat.S16)
            channels: Number of channels (default: 1 for mono)

        Example:
        >>> import numpy as np
        >>> b = np.array([1, -1, 2, -2], dtype=np.int16).tobytes()
        >>> pcm = PcmData.from_bytes(b, sample_rate=16000, format=AudioFormat.S16, channels=2)
        >>> pcm.samples.shape[0]  # channels-first
        2
        """
        # Validate format
        AudioFormat.validate(format)
        # Determine dtype and bytes per sample
        dtype: Any
        width: int
        if format == "s16":
            dtype = np.int16
            width = 2
        elif format == "f32":
            dtype = np.float32
            width = 4
        else:
            dtype = np.int16
            width = 2

        # Ensure buffer aligns to whole samples
        if len(audio_bytes) % width != 0:
            trimmed = len(audio_bytes) - (len(audio_bytes) % width)
            if trimmed <= 0:
                return cls(
                    samples=np.array([], dtype=dtype),
                    sample_rate=sample_rate,
                    format=format,
                    channels=channels,
                )
            logger.debug(
                "Trimming non-aligned PCM buffer: %d -> %d bytes",
                len(audio_bytes),
                trimmed,
            )
            audio_bytes = audio_bytes[:trimmed]

        arr = np.frombuffer(audio_bytes, dtype=dtype)
        if channels > 1 and arr.size > 0:
            # Convert interleaved [L,R,L,R,...] to shape (channels, samples)
            total_frames = (arr.size // channels) * channels
            if total_frames != arr.size:
                logger.debug(
                    "Trimming interleaved frames to channel multiple: %d -> %d elements",
                    arr.size,
                    total_frames,
                )
                arr = arr[:total_frames]
            try:
                frames = arr.reshape(-1, channels)
                arr = frames.T
            except Exception:
                logger.warning(
                    f"Unable to reshape audio buffer to {channels} channels; falling back to 1D"
                )
        return cls(
            samples=arr, sample_rate=sample_rate, format=format, channels=channels
        )

    @classmethod
    def from_numpy(
        cls,
        array: NDArray,
        sample_rate: int = 16000,
        format: AudioFormatType = AudioFormat.S16,
        channels: int = 1,
    ) -> "PcmData":
        """Build from numpy arrays with automatic dtype/shape conversion.

        Args:
            array: Input audio data as numpy array
            sample_rate: Sample rate in Hz (default: 16000)
            format: Audio format (default: AudioFormat.S16)
            channels: Number of channels (default: 1 for mono)

        Example:
        >>> import numpy as np
        >>> PcmData.from_numpy(np.array([1, 2], np.int16), sample_rate=16000, format=AudioFormat.S16, channels=1).channels
        1
        """
        # Validate format
        AudioFormat.validate(format)

        if not isinstance(array, np.ndarray):
            raise TypeError(
                f"from_numpy() expects a numpy array, got {type(array).__name__}. "
                f"Use from_bytes() for bytes or from_response() for API responses."
            )

        arr = array
        # Ensure dtype aligns with format
        if format == "s16" and arr.dtype != np.int16:
            arr = arr.astype(np.int16)
        elif format == "f32" and arr.dtype != np.float32:
            arr = arr.astype(np.float32)

        # Normalize shape to (channels, samples) for multi-channel
        if arr.ndim == 2:
            if arr.shape[0] == channels:
                samples_arr = arr
            elif arr.shape[1] == channels:
                samples_arr = arr.T
            else:
                # Assume first dimension is channels if ambiguous
                samples_arr = arr
        elif arr.ndim == 1:
            if channels > 1:
                try:
                    frames = arr.reshape(-1, channels)
                    samples_arr = frames.T
                except Exception:
                    logger.warning(
                        f"Could not reshape 1D array to {channels} channels; keeping mono"
                    )
                    channels = 1
                    samples_arr = arr
            else:
                samples_arr = arr
        else:
            # Fallback
            samples_arr = arr.reshape(-1)
            channels = 1

        return cls(
            samples=samples_arr,
            sample_rate=sample_rate,
            format=format,
            channels=channels,
        )

    @classmethod
    def from_av_frame(cls, frame: "av.AudioFrame") -> "PcmData":
        """
        Create PcmData from a PyAV AudioFrame.

        This is useful for converting audio frames from aiortc/PyAV directly
        to PcmData objects for processing.

        Args:
            frame: A PyAV AudioFrame object

        Returns:
            PcmData object with audio from the frame

        Example:
            >>> import av
            >>> import numpy as np
            >>> samples = np.array([100, 200, 300], dtype=np.int16)
            >>> frame = av.AudioFrame.from_ndarray(samples.reshape(1, -1), format='s16p', layout='mono')
            >>> frame.sample_rate = 16000
            >>> pcm = PcmData.from_av_frame(frame)
            >>> pcm.sample_rate
            16000
        """
        # Extract properties from the frame
        sample_rate = frame.sample_rate
        channels = len(frame.layout.channels)

        # Convert frame format to our format string
        # PyAV uses formats like 's16p', 's16', 'fltp', 'flt'
        frame_format = frame.format.name
        if frame_format in ("s16", "s16p"):
            pcm_format = AudioFormat.S16
            dtype = np.int16
        elif frame_format in ("flt", "fltp"):
            pcm_format = AudioFormat.F32
            dtype = np.float32
        else:
            raise ValueError(
                f"Unsupported audio frame format: '{frame_format}'. "
                f"Supported formats are: s16, s16p (int16), flt, fltp (float32)"
            )

        # Handle empty frames
        if frame.samples == 0:
            if channels == 1:
                samples_array = np.array([], dtype=dtype)
            else:
                samples_array = np.zeros((channels, 0), dtype=dtype)
        else:
            # Convert frame to ndarray
            # PyAV's to_ndarray() handles both planar and packed formats
            samples_array = frame.to_ndarray()

            # Check if this is a packed format (interleaved data)
            is_packed = frame_format in ("s16", "flt")  # Non-planar formats

            # Normalize the array shape to our standard:
            # - Mono: 1D array (samples,)
            # - Stereo: 2D array (channels, samples)
            if is_packed and channels > 1:
                # Packed stereo format: PyAV returns (1, total_samples) where data is interleaved
                # We need to deinterleave: [L0,R0,L1,R1,...] -> [[L0,L1,...], [R0,R1,...]]
                flat = samples_array.flatten()
                num_frames = len(flat) // channels
                # Deinterleave: reshape to (num_frames, channels) then transpose
                samples_array = flat.reshape(num_frames, channels).T
            elif samples_array.ndim == 1:
                # Already 1D, keep as-is for mono
                if channels > 1:
                    # Should not happen, but handle it
                    samples_array = samples_array.reshape(channels, -1)
            elif samples_array.ndim == 2:
                # Planar format: (channels, samples) - this is what we want
                if samples_array.shape[0] == channels:
                    # Already (channels, samples)
                    if channels == 1:
                        # Flatten mono to 1D
                        samples_array = samples_array.flatten()
                else:
                    # Might be (samples, channels) - transpose
                    samples_array = samples_array.T
                    if channels == 1:
                        samples_array = samples_array.flatten()

        # Extract timestamps if available
        pts = frame.pts if hasattr(frame, "pts") else None
        dts = frame.dts if hasattr(frame, "dts") else None

        # Convert time_base from Fraction to float if present
        time_base = None
        if hasattr(frame, "time_base") and frame.time_base is not None:
            if isinstance(frame.time_base, Fraction):
                time_base = float(frame.time_base)
            else:
                time_base = frame.time_base

        return cls(
            samples=samples_array,
            sample_rate=sample_rate,
            format=pcm_format,
            channels=channels,
            pts=pts,
            dts=dts,
            time_base=time_base,
        )

    @classmethod
    def from_g711(
        cls,
        g711_data: Union[bytes, str],
        sample_rate: int = 8000,
        channels: int = 1,
        mapping: Union[G711Mapping, Literal["mulaw", "alaw"]] = G711Mapping.MULAW,
        encoding: Union[G711Encoding, Literal["raw", "base64"]] = G711Encoding.RAW,
    ) -> "PcmData":
        """Build PcmData from G.711 encoded data (μ-law or A-law).

        Args:
            g711_data: G.711 encoded audio data (bytes or base64 string)
            sample_rate: Sample rate in Hz (default: 8000)
            channels: Number of channels (default: 1 for mono)
            mapping: G.711 mapping type (default: MULAW)
            encoding: Input encoding format (default: RAW, can be BASE64).
                     If g711_data is a string, encoding is automatically set to BASE64.

        Returns:
            PcmData object with decoded audio

        Example:
            >>> import numpy as np
            >>> # Decode μ-law bytes
            >>> g711_data = bytes([0xFF, 0x7F, 0x00, 0x80])
            >>> pcm = PcmData.from_g711(g711_data, sample_rate=8000, channels=1)
            >>> pcm.sample_rate
            8000
            >>> # Decode from base64 string
            >>> g711_base64 = "//8A"
            >>> pcm = PcmData.from_g711(g711_base64, sample_rate=8000, encoding="base64")
            >>> pcm.sample_rate
            8000
        """
        # Normalize encoding to string for consistent comparisons
        # Convert enum to its string value if it's an enum
        encoding_str: str
        if isinstance(encoding, G711Encoding):
            encoding_str = encoding.value
        else:
            encoding_str = str(encoding).lower()

        # Handle string input (must be base64)
        if isinstance(g711_data, str):
            # If encoding is "raw", raise error (strings can't be raw)
            if encoding_str == "raw":
                raise TypeError(
                    "Cannot use string input with encoding='raw'. "
                    "Strings are only supported for base64-encoded data. "
                    "Either pass bytes with encoding='raw', or use encoding='base64' for string input."
                )
            # Strings are always treated as base64
            g711_bytes = base64.b64decode(g711_data)
        elif encoding_str == "base64":
            g711_bytes = base64.b64decode(g711_data)
        else:
            g711_bytes = g711_data

        # Convert to numpy array of uint8
        g711_samples = np.frombuffer(g711_bytes, dtype=np.uint8)

        # Decode using appropriate lookup table
        if mapping in (G711Mapping.MULAW, "mulaw"):
            samples = MULAW_DECODE_TABLE[g711_samples]
        elif mapping in (G711Mapping.ALAW, "alaw"):
            samples = ALAW_DECODE_TABLE[g711_samples]
        else:
            raise ValueError(f"Invalid mapping: {mapping}. Must be 'mulaw' or 'alaw'")

        # Handle multi-channel: reshape if needed
        if channels > 1:
            # G.711 is typically interleaved for multi-channel
            total_samples = len(samples)
            frames = total_samples // channels
            if frames * channels == total_samples:
                # Reshape to (channels, frames) format
                samples = samples.reshape(frames, channels).T
            else:
                # If not evenly divisible, keep as 1D and let PcmData handle it
                pass

        return cls(
            samples=samples,
            sample_rate=sample_rate,
            format=AudioFormat.S16,
            channels=channels,
        )

    def resample(
        self,
        target_sample_rate: int,
        target_channels: Optional[int] = None,
    ) -> "PcmData":
        """Resample to target sample rate/channels

        Example:
        >>> import numpy as np
        >>> pcm = PcmData(samples=np.arange(8, dtype=np.int16), sample_rate=16000, format="s16", channels=1)
        >>> pcm.resample(16000, target_channels=2).channels
        2
        """
        if target_channels is None:
            target_channels = self.channels
        if self.sample_rate == target_sample_rate and target_channels == self.channels:
            return self

        # Use PyAV resampler for audio longer than 500ms, this works better than ours but it is stateful and does not work
        # well with small chunks (eg. webrtc 20ms chunks)
        if self.duration > 0.5:
            return self._resample_with_pyav(target_sample_rate, target_channels)

        # Use in-house resampler for shorter audio (lower latency)
        resampler = Resampler(
            format=self.format, sample_rate=target_sample_rate, channels=target_channels
        )
        return resampler.resample(self)

    def _resample_with_pyav(
        self, target_sample_rate: int, target_channels: int
    ) -> "PcmData":
        """Resample using PyAV (libav) for high-quality resampling and downmixing."""
        # Create AudioFrame from PcmData (preserves format: f32 -> fltp, s16 -> s16p)
        frame = self.to_av_frame()

        # Determine PyAV format based on original format to preserve it
        # f32 -> fltp (float32 planar), s16 -> s16p (int16 planar)
        if self.format in (AudioFormat.F32, "f32", "float32"):
            av_format = "fltp"
            target_format = AudioFormat.F32
        else:
            av_format = "s16p"
            target_format = AudioFormat.S16

        # Create PyAV resampler with format matching the original
        resampler = av.AudioResampler(
            format=av_format,
            layout="mono" if target_channels == 1 else "stereo",
            rate=target_sample_rate,
        )

        # Resample
        resampled_frames = resampler.resample(frame)

        # Flush the resampler to get any remaining buffered samples
        flush_frames = resampler.resample(None)
        resampled_frames.extend(flush_frames)

        # Convert each frame to PcmData using from_av_frame and concatenate them
        # Start with an empty PcmData preserving the original format
        result = PcmData(
            sample_rate=target_sample_rate,
            format=target_format,
            channels=target_channels,
        )

        for resampled_frame in resampled_frames:
            result = result.append(PcmData.from_av_frame(resampled_frame))

        return result

    def to_bytes(self) -> bytes:
        """Return interleaved PCM bytes.

        Example:
        >>> import numpy as np
        >>> pcm = PcmData(samples=np.array([[1, -1]], np.int16), sample_rate=16000, format="s16", channels=1)
        >>> len(pcm.to_bytes()) > 0
        True
        """
        arr = self.samples
        if isinstance(arr, np.ndarray):
            if arr.ndim == 2:
                channels = int(self.channels or arr.shape[0])
                # Normalize to (channels, samples)
                if arr.shape[0] == channels:
                    cmaj = arr
                elif arr.shape[1] == channels:
                    cmaj = arr.T
                else:
                    logger.warning(
                        "to_bytes: ambiguous array shape %s for channels=%d; assuming time-major",
                        arr.shape,
                        channels,
                    )
                    cmaj = arr.T
                samples_count = cmaj.shape[1]
                # Interleave channels explicitly to avoid any stride-related surprises
                out = np.empty(samples_count * channels, dtype=cmaj.dtype)
                for i in range(channels):
                    out[i::channels] = cmaj[i]
                return out.tobytes()
            return arr.tobytes()
        # Fallback
        if isinstance(arr, (bytes, bytearray)):
            return bytes(arr)
        return bytes(arr)

    def to_wav_bytes(self) -> bytes:
        """Return WAV bytes (header + frames).

        Example:
        >>> import numpy as np
        >>> pcm = PcmData(samples=np.array([0, 0], np.int16), sample_rate=16000, format="s16", channels=1)
        >>> with open("out.wav", "wb") as f:  # write to disk
        ...     _ = f.write(pcm.to_wav_bytes())
        """
        pcm_s16 = self.to_int16()
        frames = pcm_s16.to_bytes()
        width = 2

        buf = io.BytesIO()
        with wave.open(buf, "wb") as wf:
            wf.setnchannels(self.channels or 1)
            wf.setsampwidth(width)
            wf.setframerate(self.sample_rate)
            wf.writeframes(frames)
        return buf.getvalue()

    def to_av_frame(self) -> "av.AudioFrame":
        """Convert PcmData to a PyAV AudioFrame.

        Returns:
            av.AudioFrame: A PyAV AudioFrame with the audio data

        Example:
            >>> import numpy as np
            >>> pcm = PcmData(samples=np.array([100, 200], np.int16), sample_rate=8000, format="s16", channels=1)
            >>> frame = pcm.to_av_frame()
            >>> frame.sample_rate
            8000
        """
        # Determine PyAV format based on PcmData format
        # Preserve original format: f32 -> fltp (float32 planar), s16 -> s16p (int16 planar)
        if self.format in (AudioFormat.F32, "f32", "float32"):
            pcm_formatted = self.to_float32()
            av_format = "fltp"  # Float32 planar
        else:
            pcm_formatted = self.to_int16()
            av_format = "s16p"  # Int16 planar

        # Get samples and ensure correct shape for PyAV (channels, samples)
        samples = pcm_formatted.samples

        # Handle shape for PyAV
        if samples.ndim == 2:
            # Already in (channels, samples) format
            if samples.shape[0] != pcm_formatted.channels:
                # Transpose if needed
                samples = (
                    samples.T if samples.shape[1] == pcm_formatted.channels else samples
                )
        else:
            # 1D mono - reshape to (1, samples)
            samples = samples.reshape(1, -1)

        # Create PyAV AudioFrame
        layout = "mono" if pcm_formatted.channels == 1 else "stereo"
        frame = av.AudioFrame.from_ndarray(samples, format=av_format, layout=layout)
        frame.sample_rate = pcm_formatted.sample_rate
        frame.pts = pcm_formatted.pts
        return frame

    def g711_bytes(
        self,
        sample_rate: int = 8000,
        channels: int = 1,
        mapping: Union[G711Mapping, Literal["mulaw", "alaw"]] = G711Mapping.MULAW,
    ) -> bytes:
        """Encode PcmData to G.711 bytes (μ-law or A-law).

        Args:
            sample_rate: Target sample rate (default: 8000)
            channels: Target number of channels (default: 1)
            mapping: G.711 mapping type (default: MULAW)

        Returns:
            G.711 encoded bytes

        Example:
            >>> import numpy as np
            >>> pcm = PcmData(samples=np.array([100, 200], np.int16), sample_rate=8000, format="s16", channels=1)
            >>> g711 = pcm.g711_bytes()
            >>> len(g711) > 0
            True
        """
        # Resample and convert to int16 if needed (no-ops if already correct)
        pcm = self.resample(sample_rate, target_channels=channels).to_int16()

        # Encode to G.711 using PyAV codec
        if mapping in (G711Mapping.MULAW, "mulaw"):
            return self._encode_g711_with_pyav(pcm, sample_rate, channels, "pcm_mulaw")
        elif mapping in (G711Mapping.ALAW, "alaw"):
            return self._encode_g711_with_pyav(pcm, sample_rate, channels, "pcm_alaw")
        else:
            raise ValueError(f"Invalid mapping: {mapping}. Must be 'mulaw' or 'alaw'")

    def _encode_g711_with_pyav(
        self, pcm: "PcmData", sample_rate: int, channels: int, codec_name: str
    ) -> bytes:
        """Encode PcmData to G.711 using PyAV codec (pcm_mulaw or pcm_alaw)."""
        # Check if we have any samples
        if pcm.samples.size == 0:
            return b""

        # Create AudioFrame from PcmData
        frame = pcm.to_av_frame()

        # Encode the frame using PyAV codec
        return self._encode_frame_with_codec(frame, codec_name)

    def _encode_frame_with_codec(self, frame: av.AudioFrame, codec_name: str) -> bytes:
        """Encode a single AudioFrame using the specified G.711 codec."""
        # Create codec context
        # Note: PyAV type stubs are incomplete for audio codec context attributes
        codec = av.CodecContext.create(codec_name, "w")
        codec.format = "s16"  # type: ignore[attr-defined]
        codec.layout = frame.layout.name  # type: ignore[attr-defined]
        codec.sample_rate = frame.sample_rate  # type: ignore[attr-defined]
        # Set time_base to match sample rate (1/sample_rate)
        codec.time_base = fractions.Fraction(1, frame.sample_rate)
        codec.open()

        # Encode the frame
        packets = codec.encode(frame)  # type: ignore[attr-defined]

        # Get bytes from packets
        encoded_bytes = b"".join(bytes(p) for p in packets)

        # Flush the encoder to get any remaining buffered data
        flush_packets = codec.encode()  # type: ignore[attr-defined]
        if flush_packets:
            encoded_bytes += b"".join(bytes(p) for p in flush_packets)

        return encoded_bytes

    def to_float32(self) -> "PcmData":
        """Convert samples to float32 in [-1, 1].

        If the audio is already in f32 format, returns self without modification.

        Example:
        >>> import numpy as np
        >>> pcm = PcmData(samples=np.array([0, 1], np.int16), sample_rate=16000, format=AudioFormat.S16, channels=1)
        >>> pcm.to_float32().samples.dtype == np.float32
        True
        >>> # Already f32 - returns self
        >>> pcm_f32 = PcmData(samples=np.array([0.5], np.float32), sample_rate=16000, format=AudioFormat.F32)
        >>> pcm_f32.to_float32() is pcm_f32
        True
        """
        # If already f32 format, return self without modification
        if self.format in (AudioFormat.F32, "f32", "float32"):
            # Additional check: verify the samples are actually float32
            if self.samples.dtype == np.float32:
                return self

        arr = self.samples

        # Convert to float32 and scale if needed
        fmt = (self.format or "").lower()
        if fmt in ("s16", "int16") or arr.dtype == np.int16:
            arr_f32 = arr.astype(np.float32) / 32768.0
        else:
            # Ensure dtype float32; values assumed already in [-1, 1]
            arr_f32 = arr.astype(np.float32, copy=False)

        return PcmData(
            sample_rate=self.sample_rate,
            format="f32",
            samples=arr_f32,
            pts=self.pts,
            dts=self.dts,
            time_base=self.time_base,
            channels=self.channels,
            participant=self.participant,
        )

    def to_int16(self) -> "PcmData":
        """Convert samples to int16 PCM format.

        If the audio is already in s16 format, returns self without modification.

        Example:
        >>> import numpy as np
        >>> pcm = PcmData(samples=np.array([0.5, -0.5], np.float32), sample_rate=16000, format=AudioFormat.F32, channels=1)
        >>> pcm.to_int16().samples.dtype == np.int16
        True
        >>> # Already s16 - returns self
        >>> pcm_s16 = PcmData(samples=np.array([100], np.int16), sample_rate=16000, format=AudioFormat.S16)
        >>> pcm_s16.to_int16() is pcm_s16
        True
        """
        # If already s16 format, return self without modification
        if self.format in (AudioFormat.S16, "s16", "int16"):
            # Additional check: verify the samples are actually int16
            if self.samples.dtype == np.int16:
                return self

        arr = self.samples

        # Convert to int16 and scale if needed
        fmt = (self.format or "").lower()
        if fmt in ("f32", "float32") or arr.dtype == np.float32:
            # Convert float32 in [-1, 1] to int16
            arr_s16 = (np.clip(arr, -1.0, 1.0) * 32767.0).astype(np.int16)
        else:
            # Ensure dtype int16
            arr_s16 = arr.astype(np.int16, copy=False)

        return PcmData(
            sample_rate=self.sample_rate,
            format="s16",
            samples=arr_s16,
            pts=self.pts,
            dts=self.dts,
            time_base=self.time_base,
            channels=self.channels,
            participant=self.participant,
        )

    def append(self, other: "PcmData") -> "PcmData":
        """Append another chunk in-place after adjusting it to match self.

        Modifies this PcmData object and returns self for chaining.

        Example:
        >>> import numpy as np
        >>> a = PcmData(sample_rate=16000, format="s16", samples=np.array([1, 2], np.int16), channels=1)
        >>> b = PcmData(sample_rate=16000, format="s16", samples=np.array([3, 4], np.int16), channels=1)
        >>> _ = a.append(b)  # modifies a in-place
        >>> a.samples.tolist()
        [1, 2, 3, 4]
        """

        # Early exits for empty cases
        def _is_empty(arr: Any) -> bool:
            try:
                return isinstance(arr, np.ndarray) and arr.size == 0
            except Exception:
                return False

        # Samples are always numpy arrays
        def _ensure_ndarray(pcm: "PcmData") -> np.ndarray:
            return pcm.samples

        # Adjust other to match sample rate and channels first
        other_adj = other
        if (
            other_adj.sample_rate != self.sample_rate
            or other_adj.channels != self.channels
        ):
            other_adj = other_adj.resample(
                self.sample_rate, target_channels=self.channels
            )

        # Then adjust format to match
        fmt = (self.format or "").lower()
        if fmt in ("f32", "float32"):
            other_adj = other_adj.to_float32()
        elif fmt in ("s16", "int16"):
            other_adj = other_adj.to_int16()
        else:
            # For unknown formats, fallback to bytes round-trip in self's format
            other_adj = PcmData.from_bytes(
                other_adj.to_bytes(),
                sample_rate=self.sample_rate,
                format=self.format,
                channels=self.channels,
            )

        # Ensure ndarrays for concatenation
        self_arr = _ensure_ndarray(self)
        other_arr = _ensure_ndarray(other_adj)

        # If self is empty, replace with other while preserving self's metadata
        if _is_empty(self_arr):
            # Conform shape to target channels semantics and dtype
            if isinstance(other_arr, np.ndarray):
                if (self.channels or 1) == 1 and other_arr.ndim > 1:
                    other_arr = other_arr.reshape(-1)
                target_dtype = (
                    np.float32
                    if (self.format or "").lower() in ("f32", "float32")
                    else np.int16
                )
                other_arr = other_arr.astype(target_dtype, copy=False)
            self.samples = other_arr
            return self
        if _is_empty(other_arr):
            return self

        ch = max(1, int(self.channels or 1))

        # Concatenate respecting shape conventions
        if ch == 1:
            # Mono: keep 1D shape
            if self_arr.ndim > 1:
                self_arr = self_arr.reshape(-1)
            if other_arr.ndim > 1:
                other_arr = other_arr.reshape(-1)
            out = np.concatenate([self_arr, other_arr])
            # Enforce dtype based on format
            if (self.format or "").lower() in (
                "f32",
                "float32",
            ) and out.dtype != np.float32:
                out = out.astype(np.float32)
            elif (self.format or "").lower() in (
                "s16",
                "int16",
            ) and out.dtype != np.int16:
                out = out.astype(np.int16)
            self.samples = out
            return self
        else:
            # Multi-channel: normalize to (channels, samples)
            def _to_cmaj(arr: np.ndarray, channels: int) -> np.ndarray:
                if arr.ndim == 2:
                    if arr.shape[0] == channels:
                        return arr
                    if arr.shape[1] == channels:
                        return arr.T
                    # Ambiguous; assume time-major and transpose
                    return arr.T
                # 1D input: replicate across channels
                return np.tile(arr.reshape(1, -1), (channels, 1))

            self_cmaj = _to_cmaj(self_arr, ch)
            other_cmaj = _to_cmaj(other_arr, ch)
            out = np.concatenate([self_cmaj, other_cmaj], axis=1)
            # Enforce dtype based on format
            if (self.format or "").lower() in (
                "f32",
                "float32",
            ) and out.dtype != np.float32:
                out = out.astype(np.float32)
            elif (self.format or "").lower() in (
                "s16",
                "int16",
            ) and out.dtype != np.int16:
                out = out.astype(np.int16)

            self.samples = out
            return self

    def copy(self) -> "PcmData":
        """Create a deep copy of this PcmData object.

        Returns a new PcmData instance with copied samples and metadata,
        allowing independent modifications without affecting the original.

        Example:
        >>> import numpy as np
        >>> a = PcmData(sample_rate=16000, format="s16", samples=np.array([1, 2], np.int16), channels=1)
        >>> b = a.copy()
        >>> _ = b.append(PcmData(sample_rate=16000, format="s16", samples=np.array([3, 4], np.int16), channels=1))
        >>> a.samples.tolist()  # original unchanged
        [1, 2]
        >>> b.samples.tolist()  # copy was modified
        [1, 2, 3, 4]
        """
        return PcmData(
            sample_rate=self.sample_rate,
            format=self.format,
            samples=self.samples.copy(),
            pts=self.pts,
            dts=self.dts,
            time_base=self.time_base,
            channels=self.channels,
            participant=self.participant,
        )

    def clear(self) -> None:
        """Clear all samples in this PcmData object in-place.

        Similar to list.clear() or dict.clear(), this method removes all samples
        from the PcmData object while preserving all other metadata (sample_rate,
        format, channels, timestamps, etc.).

        Returns None to match the behavior of standard Python collection methods.

        Example:
        >>> import numpy as np
        >>> a = PcmData(sample_rate=16000, format="s16", samples=np.array([1, 2, 3], np.int16), channels=1)
        >>> a.clear()
        >>> len(a.samples)
        0
        >>> a.sample_rate
        16000
        """
        # Determine the appropriate dtype based on format
        fmt = (self.format or "").lower()
        if fmt in ("f32", "float32"):
            dtype = np.float32
        else:
            dtype = np.int16

        self.samples = np.array([], dtype=dtype)

    @staticmethod
    def _calculate_sample_width(format: AudioFormatType) -> int:
        """Calculate bytes per sample for a given format."""
        return 2 if format == "s16" else 4 if format == "f32" else 2

    @classmethod
    def _process_iterator_chunk(
        cls,
        buf: bytearray,
        frame_width: int,
        sample_rate: int,
        channels: int,
        format: AudioFormatType,
    ) -> tuple[Optional["PcmData"], bytearray]:
        """
        Process buffered audio data and return aligned chunk.

        Returns:
            Tuple of (PcmData chunk or None, remaining buffer)
        """
        aligned = (len(buf) // frame_width) * frame_width
        if aligned:
            chunk = bytes(buf[:aligned])
            remaining = buf[aligned:]
            pcm = cls.from_bytes(
                chunk,
                sample_rate=sample_rate,
                channels=channels,
                format=format,
            )
            return pcm, bytearray(remaining)
        return None, buf

    @classmethod
    def _finalize_iterator_buffer(
        cls,
        buf: bytearray,
        frame_width: int,
        sample_rate: int,
        channels: int,
        format: AudioFormatType,
    ) -> Optional["PcmData"]:
        """
        Process remaining buffer at end of iteration with padding if needed.

        Returns:
            Final PcmData chunk or None if buffer is empty
        """
        if not buf:
            return None

        # Pad to frame boundary
        pad_len = (-len(buf)) % frame_width
        if pad_len:
            buf.extend(b"\x00" * pad_len)

        return cls.from_bytes(
            bytes(buf),
            sample_rate=sample_rate,
            channels=channels,
            format=format,
        )

    @classmethod
    def from_response(
        cls,
        response: Any,
        *,
        sample_rate: int = 16000,
        channels: int = 1,
        format: AudioFormatType = AudioFormat.S16,
    ) -> Union["PcmData", Iterator["PcmData"], AsyncIterator["PcmData"]]:
        """Normalize provider response to PcmData or iterators of it.

        Args:
            response: Audio response (bytes, iterator, or async iterator)
            sample_rate: Sample rate in Hz (default: 16000)
            channels: Number of channels (default: 1)
            format: Audio format (default: AudioFormat.S16)

        Example:
        >>> PcmData.from_response(bytes([0, 0]), sample_rate=16000, format=AudioFormat.S16).sample_rate
        16000
        """
        # Validate format
        AudioFormat.validate(format)

        # bytes-like returns a single PcmData
        if isinstance(response, (bytes, bytearray, memoryview)):
            return cls.from_bytes(
                bytes(response),
                sample_rate=sample_rate,
                channels=channels,
                format=format,
            )

        # Already a PcmData
        if isinstance(response, PcmData):
            return response

        # Async iterator
        if hasattr(response, "__aiter__"):

            async def _agen():
                width = cls._calculate_sample_width(format)
                frame_width = width * max(1, channels)
                buf = bytearray()

                async for item in response:
                    if isinstance(item, PcmData):
                        yield item
                        continue

                    data = getattr(item, "data", item)
                    if not isinstance(data, (bytes, bytearray, memoryview)):
                        raise TypeError("Async iterator yielded unsupported item type")

                    buf.extend(bytes(data))
                    chunk, buf = cls._process_iterator_chunk(
                        buf, frame_width, sample_rate, channels, format
                    )
                    if chunk:
                        yield chunk

                # Handle remainder
                final_chunk = cls._finalize_iterator_buffer(
                    buf, frame_width, sample_rate, channels, format
                )
                if final_chunk:
                    yield final_chunk

            return _agen()

        # Sync iterator (but skip treating bytes as iterable of ints)
        if hasattr(response, "__iter__") and not isinstance(
            response, (str, bytes, bytearray, memoryview)
        ):

            def _gen():
                width = cls._calculate_sample_width(format)
                frame_width = width * max(1, channels)
                buf = bytearray()

                for item in response:
                    if isinstance(item, PcmData):
                        yield item
                        continue

                    data = getattr(item, "data", item)
                    if not isinstance(data, (bytes, bytearray, memoryview)):
                        raise TypeError("Iterator yielded unsupported item type")

                    buf.extend(bytes(data))
                    chunk, buf = cls._process_iterator_chunk(
                        buf, frame_width, sample_rate, channels, format
                    )
                    if chunk:
                        yield chunk

                # Handle remainder
                final_chunk = cls._finalize_iterator_buffer(
                    buf, frame_width, sample_rate, channels, format
                )
                if final_chunk:
                    yield final_chunk

            return _gen()

        # Single object with .data
        if hasattr(response, "data"):
            data = getattr(response, "data")
            if isinstance(data, (bytes, bytearray, memoryview)):
                return cls.from_bytes(
                    bytes(data),
                    sample_rate=sample_rate,
                    channels=channels,
                    format=format,
                )

        raise TypeError(
            f"Unsupported response type for PcmData.from_response: {type(response)}"
        )

    def chunks(
        self, chunk_size: int, overlap: int = 0, pad_last: bool = False
    ) -> Iterator["PcmData"]:
        """
        Iterate over fixed-size chunks of audio data.

        Args:
            chunk_size: Number of samples per chunk
            overlap: Number of samples to overlap between chunks (for windowing)
            pad_last: If True, pad the last chunk with zeros to match chunk_size

        Yields:
            PcmData objects with chunk_size samples each

        Example:
            >>> pcm = PcmData(samples=np.arange(10, dtype=np.int16), sample_rate=16000, format="s16")
            >>> chunks = list(pcm.chunks(4, overlap=2))
            >>> len(chunks)  # [0:4], [2:6], [4:8], [6:10], [8:10]
            5
        """
        # Normalize sample array shape
        if self.samples.ndim == 2 and self.channels == 1:
            samples = self.samples.flatten()
        elif self.samples.ndim == 2:
            # For multi-channel, work with channel-major format
            samples = self.samples
        else:
            samples = self.samples

        # Handle overlap
        step = max(1, chunk_size - overlap)

        if self.channels > 1 and samples.ndim == 2:
            # Multi-channel case: chunk along the samples axis
            num_samples = samples.shape[1]
            for i in range(0, num_samples, step):
                end_idx = min(i + chunk_size, num_samples)
                chunk_samples = samples[:, i:end_idx]

                # Check if we need to pad
                if chunk_samples.shape[1] < chunk_size:
                    if pad_last and chunk_samples.shape[1] > 0:
                        pad_width = chunk_size - chunk_samples.shape[1]
                        chunk_samples = np.pad(
                            chunk_samples,
                            ((0, 0), (0, pad_width)),
                            mode="constant",
                            constant_values=0,
                        )
                    elif chunk_samples.shape[1] == 0:
                        break
                    elif not pad_last:
                        # Yield incomplete chunk if it has samples
                        pass

                # Calculate timestamp for this chunk
                chunk_pts = None
                if self.pts is not None and self.time_base is not None:
                    chunk_pts = self.pts + int(i / self.sample_rate / self.time_base)

                yield PcmData(
                    sample_rate=self.sample_rate,
                    format=self.format,
                    samples=chunk_samples,
                    pts=chunk_pts,
                    dts=self.dts,
                    time_base=self.time_base,
                    channels=self.channels,
                )
        else:
            # Mono or 1D case
            samples_1d = samples.flatten() if samples.ndim > 1 else samples
            total_samples = len(samples_1d)

            for i in range(0, total_samples, step):
                end_idx = min(i + chunk_size, total_samples)
                chunk_samples = samples_1d[i:end_idx]

                # Check if we need to pad
                if len(chunk_samples) < chunk_size:
                    if pad_last and len(chunk_samples) > 0:
                        chunk_samples = np.pad(
                            chunk_samples,
                            (0, chunk_size - len(chunk_samples)),
                            mode="constant",
                            constant_values=0,
                        )
                    elif len(chunk_samples) == 0:
                        break
                    elif not pad_last:
                        # Yield incomplete chunk if it has samples
                        pass

                # Calculate timestamp for this chunk
                chunk_pts = None
                if self.pts is not None and self.time_base is not None:
                    chunk_pts = self.pts + int(i / self.sample_rate / self.time_base)

                yield PcmData(
                    sample_rate=self.sample_rate,
                    format=self.format,
                    samples=chunk_samples,
                    pts=chunk_pts,
                    dts=self.dts,
                    time_base=self.time_base,
                    channels=1 if chunk_samples.ndim == 1 else self.channels,
                )

    def sliding_window(
        self, window_size_ms: float, hop_ms: float, pad_last: bool = False
    ) -> Iterator["PcmData"]:
        """
        Generate sliding windows for analysis (useful for feature extraction).

        Args:
            window_size_ms: Window size in milliseconds
            hop_ms: Hop size in milliseconds
            pad_last: If True, pad the last window with zeros

        Yields:
            PcmData windows of the specified size

        Example:
            >>> pcm = PcmData(samples=np.arange(800, dtype=np.int16), sample_rate=16000, format="s16")
            >>> windows = list(pcm.sliding_window(25.0, 10.0))  # 25ms window, 10ms hop
            >>> len(windows)  # 400 samples per window, 160 sample hop
            5
        """
        window_samples = int(self.sample_rate * window_size_ms / 1000)
        hop_samples = int(self.sample_rate * hop_ms / 1000)
        overlap = max(0, window_samples - hop_samples)

        return self.chunks(window_samples, overlap=overlap, pad_last=pad_last)

    def tail(
        self,
        duration_s: float,
        pad: bool = False,
        pad_at: str = "end",
    ) -> "PcmData":
        """
        Keep only the last N seconds of audio.

        Args:
            duration_s: Duration in seconds
            pad: If True, pad with zeros when audio is shorter than requested
            pad_at: Where to add padding ('start' or 'end'), default is 'end'

        Returns:
            PcmData with the last N seconds

        Example:
            >>> import numpy as np
            >>> # 10 seconds of audio at 16kHz = 160000 samples
            >>> pcm = PcmData(samples=np.arange(160000, dtype=np.int16), sample_rate=16000, format=AudioFormat.S16)
            >>> # Get last 5 seconds
            >>> tail = pcm.tail(duration_s=5.0)
            >>> tail.duration
            5.0
            >>> # Get last 8 seconds, pad at start if needed
            >>> short_pcm = PcmData(samples=np.arange(16000, dtype=np.int16), sample_rate=16000, format=AudioFormat.S16)
            >>> padded = short_pcm.tail(duration_s=8.0, pad=True, pad_at='start')
            >>> padded.duration
            8.0
        """
        target_samples = int(self.sample_rate * duration_s)

        # Validate pad_at parameter
        if pad_at not in ("start", "end"):
            raise ValueError(f"pad_at must be 'start' or 'end', got {pad_at!r}")

        # Get samples array (always ndarray)
        samples = self.samples

        # Handle multi-channel audio
        if samples.ndim == 2 and self.channels > 1:
            # Shape is (channels, samples)
            num_samples = samples.shape[1]
            if num_samples >= target_samples:
                # Truncate: keep last target_samples
                new_samples = samples[:, -target_samples:]
            elif pad:
                # Pad to reach target_samples
                pad_width = target_samples - num_samples
                if pad_at == "start":
                    new_samples = np.pad(
                        samples,
                        ((0, 0), (pad_width, 0)),
                        mode="constant",
                        constant_values=0,
                    )
                else:  # pad_at == 'end'
                    new_samples = np.pad(
                        samples,
                        ((0, 0), (0, pad_width)),
                        mode="constant",
                        constant_values=0,
                    )
            else:
                # Return as-is (shorter than requested, no padding)
                new_samples = samples
        else:
            # Mono or 1D case
            samples_1d = samples.flatten() if samples.ndim > 1 else samples
            num_samples = len(samples_1d)

            if num_samples >= target_samples:
                # Truncate: keep last target_samples
                new_samples = samples_1d[-target_samples:]
            elif pad:
                # Pad to reach target_samples
                pad_width = target_samples - num_samples
                if pad_at == "start":
                    new_samples = np.pad(
                        samples_1d, (pad_width, 0), mode="constant", constant_values=0
                    )
                else:  # pad_at == 'end'
                    new_samples = np.pad(
                        samples_1d, (0, pad_width), mode="constant", constant_values=0
                    )
            else:
                # Return as-is (shorter than requested, no padding)
                new_samples = samples_1d

        return PcmData(
            sample_rate=self.sample_rate,
            format=self.format,
            samples=new_samples,
            pts=self.pts,
            dts=self.dts,
            time_base=self.time_base,
            channels=self.channels,
            participant=self.participant,
        )

    def head(
        self,
        duration_s: float,
        pad: bool = False,
        pad_at: str = "end",
    ) -> "PcmData":
        """
        Keep only the first N seconds of audio.

        Args:
            duration_s: Duration in seconds
            pad: If True, pad with zeros when audio is shorter than requested
            pad_at: Where to add padding ('start' or 'end'), default is 'end'

        Returns:
            PcmData with the first N seconds

        Example:
            >>> import numpy as np
            >>> # 10 seconds of audio at 16kHz = 160000 samples
            >>> pcm = PcmData(samples=np.arange(160000, dtype=np.int16), sample_rate=16000, format=AudioFormat.S16)
            >>> # Get first 3 seconds
            >>> head = pcm.head(duration_s=3.0)
            >>> head.duration
            3.0
            >>> # Get first 8 seconds, pad at end if needed
            >>> short_pcm = PcmData(samples=np.arange(16000, dtype=np.int16), sample_rate=16000, format=AudioFormat.S16)
            >>> padded = short_pcm.head(duration_s=8.0, pad=True, pad_at='end')
            >>> padded.duration
            8.0
        """
        target_samples = int(self.sample_rate * duration_s)

        # Validate pad_at parameter
        if pad_at not in ("start", "end"):
            raise ValueError(f"pad_at must be 'start' or 'end', got {pad_at!r}")

        # Get samples array (always ndarray)
        samples = self.samples

        # Handle multi-channel audio
        if samples.ndim == 2 and self.channels > 1:
            # Shape is (channels, samples)
            num_samples = samples.shape[1]
            if num_samples >= target_samples:
                # Truncate: keep first target_samples
                new_samples = samples[:, :target_samples]
            elif pad:
                # Pad to reach target_samples
                pad_width = target_samples - num_samples
                if pad_at == "start":
                    new_samples = np.pad(
                        samples,
                        ((0, 0), (pad_width, 0)),
                        mode="constant",
                        constant_values=0,
                    )
                else:  # pad_at == 'end'
                    new_samples = np.pad(
                        samples,
                        ((0, 0), (0, pad_width)),
                        mode="constant",
                        constant_values=0,
                    )
            else:
                # Return as-is (shorter than requested, no padding)
                new_samples = samples
        else:
            # Mono or 1D case
            samples_1d = samples.flatten() if samples.ndim > 1 else samples
            num_samples = len(samples_1d)

            if num_samples >= target_samples:
                # Truncate: keep first target_samples
                new_samples = samples_1d[:target_samples]
            elif pad:
                # Pad to reach target_samples
                pad_width = target_samples - num_samples
                if pad_at == "start":
                    new_samples = np.pad(
                        samples_1d, (pad_width, 0), mode="constant", constant_values=0
                    )
                else:  # pad_at == 'end'
                    new_samples = np.pad(
                        samples_1d, (0, pad_width), mode="constant", constant_values=0
                    )
            else:
                # Return as-is (shorter than requested, no padding)
                new_samples = samples_1d

        return PcmData(
            sample_rate=self.sample_rate,
            format=self.format,
            samples=new_samples,
            pts=self.pts,
            dts=self.dts,
            time_base=self.time_base,
            channels=self.channels,
            participant=self.participant,
        )

    @property
    def empty(self) -> bool:
        return len(self.samples) == 0


class PyAVResampler:
    """
    A stateful audio resampler.
    It acts as a thin wrapper around `pyav.AudioResampler`, and it is intended to be
    created once for the audio track and re-used.


    Key differences from the stateless implementation:

    - `pyav.AudioResampler` buffers samples internally, so the number of output samples doesn't always match the input.
    - `PyAVResampler` keeps its own monotonic PTS clock, and it's meant to be used with a single audio stream only.
       It ignores the PTS/DTS from `PcmData`.
       PTS always starts from 0 for the first output.
    - `pyav.AudioResampler` configures itself based on the first input frame. Feeding data in a different format
       or sample rate will fail.
    - `PyAVResampler` is not thread-safe.

    The source PCMs must have the same sample rate, format, and number of channels.

    Example:

        >>> import numpy as np
        >>> resampler = PyAVResampler(format="s16", sample_rate=48000, channels=1)
        >>> # Process 20ms chunks at 16kHz (320 samples each)
        >>> samples = np.random.randint(-1000, 1000, 320, dtype=np.int16)
        >>> pcm_16k = PcmData(samples=samples, sample_rate=16000, format="s16", channels=1)
        >>> pcm_48k = resampler.resample(pcm_16k)  # Returns 912 samples at 48kHz without flushing
        >>> len(pcm_48k.samples)
        912
        >>> flushed_pcm = resampler.flush()
        >>> len(flushed_pcm.samples)
        48
    """

    def __init__(
        self,
        format: AudioFormatType,
        sample_rate: int,
        channels: int,
        frame_size: int = 0,
    ):
        """
        Initialize a stateful resampler with target audio parameters.

        Args:
            format: Target format ("s16" or "f32", also `AudioFormat.F32` or `AudioFormat.S16`).
            sample_rate: Target sample rate (e.g., 48000, 16000, 8000)
            channels: Target number of channels (1 for mono, 2 for stereo)
            frame_size: how many samples per channel are produce in each output frame.
                When set, the underlying resampler will buffer output the specified number of samples is accumulated,
                and it will output frames of this exact size (except when ".resample(flush=True)").
                Default - `0` (each frame can be of a variable size).
        """
        if isinstance(format, str):
            AudioFormat.validate(format)

        self.format = AudioFormat(format)
        self.sample_rate = sample_rate
        self.channels = channels
        self.frame_size = frame_size
        # Determine PyAV format based on original format to preserve it
        # f32 -> fltp (float32 planar), s16 -> s16p (int16 planar)
        self._pyav_format = "fltp" if self.format == AudioFormat.F32 else "s16p"
        self._pts = 0
        self._set_pyav_resampler()

    def __repr__(self) -> str:
        return (
            f"{self.__class__.__name__}(format={self.format.name.lower()!r}, "
            f"sample_rate={self.sample_rate}, channels={self.channels}, frame_size={self.frame_size})"
        )

    def _set_pyav_resampler(self):
        # Create PyAV resampler with format matching the original
        self._pyav_resampler = av.AudioResampler(
            format=self._pyav_format,
            layout="mono" if self.channels == 1 else "stereo",
            rate=self.sample_rate,
            frame_size=self.frame_size,
        )

    def _pyav_resample(self, frame: av.AudioFrame | None) -> list[av.AudioFrame]:
        if frame is not None and not frame.samples:
            # pyav resampler fails if audioframe has no samples
            return []
        return self._pyav_resampler.resample(frame)

    def resample(self, pcm: PcmData, flush: bool = False) -> PcmData:
        """
        Resample using PyAV (libav) for high-quality resampling and downmixing.

        Args:
            pcm: Input PCM data to resample
            flush: if True, get the remaining frames from underlying `av.AudioResampler` if there are any.
                Default - `False`.

        Returns:
            New PcmData object with resampled audio, potentially empty if the frame size is set and larger
            than the input PCM.
        """
        # Create AudioFrame from PcmData
        frame = pcm.to_av_frame()

        # Convert each frame to PcmData using from_av_frame and concatenate them
        # Start with an empty PcmData preserving the original format
        result = PcmData(
            sample_rate=self.sample_rate,
            format=self.format,
            channels=self.channels,
            time_base=1 / self.sample_rate,
        )

        # Resample
        # Keep the lock because resampler is stateful, and we want to keep PTS in order
        resampled_frames = self._pyav_resample(frame)
        if flush:
            try:
                resampled_frames.extend(self._pyav_resample(None))
            finally:
                # Reset the resampler because it cannot be used after it's flushed,
                self._set_pyav_resampler()

        for resampled_frame in resampled_frames:
            self._pts += resampled_frame.samples
            result = result.append(PcmData.from_av_frame(resampled_frame))

        result.pts = self._pts - len(result.samples)
        result.dts = result.pts
        return result

    def flush(self) -> PcmData:
        """
        Flush the underlying `av.AudioResampler`

        Returns:
            New PcmData object with resampled audio, potentially empty.
        """
        # Convert each frame to PcmData using from_av_frame and concatenate them
        # Start with an empty PcmData preserving the original format
        result = PcmData(
            sample_rate=self.sample_rate,
            format=self.format,
            channels=self.channels,
        )

        try:
            # Flush the resampler to get remaining buffered samples
            resampled_frames = self._pyav_resample(None)
        finally:
            # Reset the resampler because it cannot be used after it's flushed,
            self._set_pyav_resampler()

        # Convert frames to PcmData and update the PTS clock
        for resampled_frame in resampled_frames:
            self._pts += resampled_frame.samples
            result = result.append(PcmData.from_av_frame(resampled_frame))
        result.pts = self._pts - len(result.samples)
        return result


class Resampler:
    """
    Stateless audio resampler for converting between sample rates, formats, and channels.

    This resampler is designed for processing audio chunks independently without
    maintaining state between calls, making it ideal for real-time streaming where
    20ms audio chunks need to be processed without clicking artifacts.

    Uses linear interpolation for sample rate conversion, which produces accurate
    results for common conversions (e.g., 16kHz -> 48kHz) without the complexity
    of stateful resamplers.

    Example:
        >>> import numpy as np
        >>> resampler = Resampler(format="s16", sample_rate=48000, channels=1)
        >>> # Process 20ms chunks at 16kHz (320 samples each)
        >>> samples = np.zeros(320, dtype=np.int16)
        >>> pcm_16k = PcmData(samples=samples, sample_rate=16000, format="s16", channels=1)
        >>> pcm_48k = resampler.resample(pcm_16k)  # Returns 960 samples at 48kHz
        >>> len(pcm_48k.samples)
        960
    """

    def __init__(self, format: str, sample_rate: int, channels: int):
        """
        Initialize a resampler with target audio parameters.

        Args:
            format: Target format ("s16" or "f32")
            sample_rate: Target sample rate (e.g., 48000, 16000)
            channels: Target number of channels (1 for mono, 2 for stereo)
        """
        self.format: AudioFormatType = AudioFormat.validate(format)
        self.sample_rate = sample_rate
        self.channels = channels

    def resample(self, pcm: PcmData) -> PcmData:
        """
        Resample PCM data to match this resampler's configuration.

        This method:
        1. Adjusts sample rate using linear interpolation if needed
        2. Adjusts number of channels (mono <-> stereo) if needed
        3. Adjusts format (s16 <-> f32) if needed
        4. Preserves timestamps (pts, dts, time_base)

        Args:
            pcm: Input PCM data to resample

        Returns:
            New PcmData object with resampled audio
        """
        samples = pcm.samples
        current_rate = pcm.sample_rate
        current_channels = pcm.channels
        current_format = pcm.format

        # Step 1: Adjust sample rate if needed
        if current_rate != self.sample_rate:
            if current_channels == 1:
                samples = self._resample_1d(samples, current_rate, self.sample_rate)
            else:
                # Resample each channel independently
                resampled_channels = []
                for ch in range(current_channels):
                    resampled_ch = self._resample_1d(
                        samples[ch], current_rate, self.sample_rate
                    )
                    resampled_channels.append(resampled_ch)
                samples = np.array(resampled_channels)
            current_rate = self.sample_rate

        # Step 2: Adjust channels if needed
        if current_channels != self.channels:
            samples = self._adjust_channels(samples, current_channels, self.channels)
            current_channels = self.channels

        # Step 3: Adjust format if needed
        if current_format != self.format:
            samples = self._adjust_format(samples, current_format, self.format)
            current_format = self.format

        # Create new PcmData with resampled audio, preserving timestamps and participant
        return PcmData(
            samples=samples,
            sample_rate=self.sample_rate,
            format=self.format,
            channels=self.channels,
            pts=pcm.pts,
            dts=pcm.dts,
            time_base=pcm.time_base,
            participant=pcm.participant,
        )

    def _resample_1d(
        self, samples: np.ndarray, from_rate: int, to_rate: int
    ) -> np.ndarray:
        """
        Resample a 1D array using linear interpolation.

        Args:
            samples: 1D input samples
            from_rate: Input sample rate
            to_rate: Output sample rate

        Returns:
            Resampled 1D array
        """
        if from_rate == to_rate:
            return samples

        # Calculate output length
        num_samples = len(samples)
        duration = num_samples / from_rate
        out_length = int(np.round(duration * to_rate))

        if out_length == 0:
            return np.array([], dtype=samples.dtype)

        # Handle edge case: single output sample
        if out_length == 1:
            # Return the first sample
            return np.array([samples[0]], dtype=samples.dtype)

        # Create interpolation indices
        # Map output sample positions back to input sample positions
        # Use (num_samples - 1) / (out_length - 1) to ensure the last output
        # sample maps exactly to the last input sample, preventing out-of-bounds
        out_indices = np.arange(out_length)
        in_indices = out_indices * ((num_samples - 1) / (out_length - 1))

        # Linear interpolation
        resampled = np.interp(in_indices, np.arange(num_samples), samples)

        return resampled.astype(samples.dtype)

    def _adjust_channels(
        self, samples: np.ndarray, from_channels: int, to_channels: int
    ) -> np.ndarray:
        """
        Adjust number of channels (mono <-> stereo conversion).

        Args:
            samples: Input samples
            from_channels: Input channel count
            to_channels: Output channel count

        Returns:
            Samples with adjusted channel count
        """
        if from_channels == to_channels:
            return samples

        if from_channels == 1 and to_channels == 2:
            # Mono to stereo: duplicate the mono channel
            return np.array([samples, samples])
        elif from_channels == 2 and to_channels == 1:
            # Stereo to mono: average the two channels
            return np.mean(samples, axis=0).astype(samples.dtype)
        else:
            raise ValueError(
                f"Unsupported channel conversion: {from_channels} -> {to_channels}"
            )

    def _adjust_format(
        self, samples: np.ndarray, from_format: str, to_format: str
    ) -> np.ndarray:
        """
        Convert between s16 and f32 formats.

        Args:
            samples: Input samples
            from_format: Input format ("s16" or "f32")
            to_format: Output format ("s16" or "f32")

        Returns:
            Samples in the target format
        """
        if from_format == to_format:
            return samples

        if from_format == "s16" and to_format == "f32":
            # Convert int16 to float32 in range [-1, 1]
            # Clip values before conversion to prevent overflow
            clipped = np.clip(samples, -32768, 32767)
            return (clipped / 32768.0).astype(np.float32)
        elif from_format == "f32" and to_format == "s16":
            # Convert float32 to int16
            # Clip to [-1, 1] range first
            clipped = np.clip(samples, -1.0, 1.0)
            return (clipped * 32767.0).astype(np.int16)
        else:
            raise ValueError(
                f"Unsupported format conversion: {from_format} -> {to_format}"
            )

    def __repr__(self) -> str:
        return (
            f"{self.__class__.__name__}(format={self.format!r}, "
            f"sample_rate={self.sample_rate}, channels={self.channels})"
        )


def patch_sdp_offer(sdp: str) -> str:
    """
    Patches an SDP offer to ensure consistent ICE and DTLS parameters across all media sections.

    This function:
    1. Ensures all media descriptions have the same ice-ufrag, ice-pwd, and fingerprint values
       (using values from the first media section)
    2. Sets all media descriptions' ports to match the first media description's port
    3. Replaces all media descriptions' candidates with candidates from the first media description

    Args:
        sdp: The original SDP string.

    Returns:
        The modified SDP string with consistent parameters across all media sections.
    """
    # Parse the SDP
    session = aiortc.sdp.SessionDescription.parse(sdp)

    # If we have fewer than 2 media sections, nothing to patch
    if len(session.media) < 2:
        return sdp

    # Get the values from the first media section
    first_media = session.media[0]
    reference_port = first_media.port
    reference_ice = first_media.ice
    reference_fingerprints = first_media.dtls.fingerprints if first_media.dtls else []
    reference_candidates = first_media.ice_candidates

    # Apply to all other media sections
    for media in session.media[1:]:
        # Update port
        media.port = reference_port

        # Update ICE parameters
        if reference_ice and media.ice:
            media.ice.usernameFragment = reference_ice.usernameFragment
            media.ice.password = reference_ice.password
            media.ice.iceLite = reference_ice.iceLite

        # Update DTLS fingerprints
        if media.dtls and reference_fingerprints:
            media.dtls.fingerprints = reference_fingerprints.copy()

        # Replace ICE candidates
        media.ice_candidates = reference_candidates.copy()
        if reference_candidates:
            media.ice_candidates_complete = True

    # Convert back to string
    return str(session)


def fix_sdp_msid_semantic(sdp: str) -> str:
    """
    Fix SDP msid-semantic format by ensuring there is a space after "WMS".

    The WebRTC spec requires a space between "WMS" and any identifiers.
    Some SDPs may incorrectly have "WMS*" instead of "WMS *" which can
    cause connection issues.

    Args:
        sdp: The SDP string to fix

    Returns:
        The fixed SDP string
    """
    return re.sub(r"a=msid-semantic:WMS\*", r"a=msid-semantic:WMS *", sdp)


def fix_sdp_rtcp_fb(sdp: str) -> str:
    """
    Fix SDP rtcp-fb format
    https://github.com/pion/webrtc/issues/3207
    """
    # Some generators (e.g. pion) emit a trailing space after feedback id when no
    # parameter is present, e.g. "a=rtcp-fb:96 goog-remb ". This breaks some
    # parsers. Strip only the trailing whitespace before end-of-line on rtcp-fb
    # lines while preserving CRLF if present.
    #
    # Example fix:
    #   a=rtcp-fb:96 goog-remb \r\n  ->  a=rtcp-fb:96 goog-remb\r\n
    return re.sub(
        r"(?m)^(a=rtcp-fb:[^\r\n]*\S)[ \t]+(?=\r?$)",
        r"\1",
        sdp,
    )


def parse_track_stream_mapping(sdp: str) -> dict:
    """Parse SDP to extract track_id to stream_id mapping from msid lines."""
    mapping = {}
    for line in sdp.split("\n"):
        if line.startswith("a=msid:"):
            parts = line.strip().split(" ")
            if len(parts) >= 2:
                # Format: a=msid:stream_id track_id
                track_id = parts[1]
                stream_id = parts[0].replace("a=msid:", "")
                mapping[track_id] = stream_id
    return mapping


class BufferedMediaTrack(aiortc.mediastreams.MediaStreamTrack):
    """A wrapper for MediaStreamTrack that buffers one peeked frame.

    Also tracks video frame statistics when kind is 'video':
    - frames_processed: total frames that passed through recv()
    - frame_width, frame_height: dimensions of the last frame
    - total_processing_time_ms: cumulative time spent in recv()
    """

    def __init__(self, track):
        super().__init__()
        self._track = track
        self._buffered_frames = []  # Store multiple frames
        self._kind = track.kind
        self._id = track.id
        self._ended = False

        # Frame statistics (for video tracks)
        self.frames_processed: int = 0
        self.frame_width: int = 0
        self.frame_height: int = 0
        self.total_processing_time_ms: float = 0.0

    @property
    def kind(self):
        return self._kind

    @property
    def id(self):
        return self._id

    @property
    def readyState(self):
        return "ended" if self._ended else self._track.readyState

    def get_frame_stats(self) -> Dict[str, Any]:
        """Get current frame statistics for StatsTracer injection."""
        return {
            "framesSent": self.frames_processed,
            "frameWidth": self.frame_width,
            "frameHeight": self.frame_height,
            "totalEncodeTime": self.total_processing_time_ms / 1000.0,
        }

    def _update_frame_stats(self, frame, processing_time_ms: float) -> None:
        """Update frame statistics from a video frame."""
        if (
            self._kind == "video"
            and hasattr(frame, "width")
            and hasattr(frame, "height")
        ):
            self.frames_processed += 1
            self.frame_width = frame.width
            self.frame_height = frame.height
            self.total_processing_time_ms += processing_time_ms

    async def recv(self):
        """Returns the next buffered frame if available, otherwise gets a new frame from the track."""
        if self._ended:
            raise MediaStreamError("Track is ended")

        if self._buffered_frames:
            # Return the oldest buffered frame (FIFO order)
            frame = self._buffered_frames.pop(0)
            self._update_frame_stats(frame, 0.0)
            return frame

        start_time = time.monotonic()
        try:
            frame = await self._track.recv()
            elapsed_ms = (time.monotonic() - start_time) * 1000
            self._update_frame_stats(frame, elapsed_ms)
            return frame
        except Exception as e:
            logger.error(f"Error receiving frame from track: {e}")
            self._ended = True
            raise MediaStreamError(f"Error receiving frame: {e}") from e

    async def peek(self):
        """Peek at the next frame without removing it from the stream."""
        if self._ended:
            raise MediaStreamError("Track is ended")

        if not self._buffered_frames:
            try:
                # Buffer a new frame
                frame = await self._track.recv()
                self._buffered_frames.append(frame)
            except Exception as e:
                logger.error(f"Error peeking at frame: {e}")
                self._ended = True
                raise MediaStreamError(f"Error peeking at frame: {e}") from e

        # Return the next frame that would be received, but don't remove it
        if self._buffered_frames:
            return self._buffered_frames[0]
        return None

    def stop(self):
        """Stop the track and clean up resources."""
        if not self._ended:
            self._ended = True
            self._buffered_frames = []  # Clear all buffered frames
            # Stop the underlying track if it has a stop method
            if hasattr(self._track, "stop"):
                try:
                    self._track.stop()
                except Exception as e:
                    logger.error(f"Error stopping track: {e}")


class VideoFrameTracker(aiortc.mediastreams.MediaStreamTrack):
    """A transparent wrapper that tracks video frame statistics.

    Used for subscriber video tracks to capture frame metrics that aiortc
    doesn't provide natively (dimensions, frame count, decode time).
    """

    kind = "video"

    def __init__(self, track: MediaStreamTrack):
        super().__init__()
        self._track = track
        self._id = track.id
        self._ended = False

        # Frame statistics
        self.frames_processed: int = 0
        self.frame_width: int = 0
        self.frame_height: int = 0
        self.total_processing_time_ms: float = 0.0

    @property
    def id(self):
        return self._id

    @property
    def readyState(self):
        return "ended" if self._ended else self._track.readyState

    def get_frame_stats(self) -> Dict[str, Any]:
        """Get current frame statistics for StatsTracer injection."""
        return {
            "framesDecoded": self.frames_processed,
            "frameWidth": self.frame_width,
            "frameHeight": self.frame_height,
            "totalDecodeTime": self.total_processing_time_ms / 1000.0,
        }

    async def recv(self):
        """Receive a frame, tracking statistics."""
        if self._ended:
            raise MediaStreamError("Track is ended")

        start_time = time.monotonic()
        try:
            frame = await self._track.recv()
            elapsed_ms = (time.monotonic() - start_time) * 1000

            # Update stats for video frames
            if isinstance(frame, av.VideoFrame):
                self.frames_processed += 1
                self.frame_width = frame.width
                self.frame_height = frame.height
                self.total_processing_time_ms += elapsed_ms

            return frame
        except MediaStreamError:
            self._ended = True
            raise
        except Exception as e:
            logger.error(f"Error receiving frame: {e}")
            self._ended = True
            raise MediaStreamError(f"Error receiving frame: {e}") from e

    def stop(self):
        """Stop the track."""
        if not self._ended:
            self._ended = True
            if hasattr(self._track, "stop"):
                self._track.stop()


async def detect_video_properties(
    video_track: aiortc.mediastreams.MediaStreamTrack,
) -> Dict[str, Any]:
    """
    Detect video track properties by peeking at frames.

    Args:
        video_track: A video MediaStreamTrack

    Returns:
        Dict containing width (int), height (int), fps (int), and bitrate (int) in kbps
    """
    logger.info("Detecting video track properties")

    # Default properties in case of failure
    default_properties = {"width": 640, "height": 480, "fps": 30, "bitrate": 800}

    if not video_track or video_track.kind != "video":
        logger.warning("No video track provided or track is not video")
        return default_properties

    # Flag to indicate if we created our own buffered track
    own_buffered_track = False
    buffered_track = None

    try:
        # Ensure we're using a buffered track
        if isinstance(video_track, BufferedMediaTrack):
            buffered_track = video_track
        else:
            buffered_track = BufferedMediaTrack(video_track)
            own_buffered_track = True

        # Peek at a frame to get dimensions
        frame1 = await asyncio.wait_for(buffered_track.peek(), timeout=2.0)

        if not frame1:
            logger.warning("No frame received from video track")
            return default_properties

        # Extract width and height
        width = getattr(frame1, "width", default_properties["width"])
        height = getattr(frame1, "height", default_properties["height"])

        # Calculate FPS based on time delta between consecutive frames
        fps = 30  # Default value
        try:
            # Consume the first frame but store its pts and time_base
            frame1 = await buffered_track.recv()
            frame1_pts = getattr(frame1, "pts", None)
            time_base = getattr(frame1, "time_base", None)

            # Get the second frame
            frame2 = await asyncio.wait_for(buffered_track.recv(), timeout=2.0)
            frame2_pts = getattr(frame2, "pts", None)

            # Calculate FPS if we have all the necessary information
            if (
                frame1_pts is not None
                and frame2_pts is not None
                and time_base is not None
            ):
                delta_ticks = frame2_pts - frame1_pts
                delta_seconds = delta_ticks * time_base

                if delta_seconds > 0:
                    estimated_fps = 1 / delta_seconds
                    fps = int(round(estimated_fps))
                    logger.info(f"Calculated FPS: {fps} (delta: {delta_seconds}s)")
                else:
                    logger.warning("Cannot calculate FPS: zero or negative time delta")
            else:
                logger.warning(
                    "Cannot calculate FPS: missing PTS or time_base information"
                )
        except Exception as e:
            logger.warning(f"Error calculating FPS: {e}, using default 30 fps")

        # Calculate a dynamic bitrate based on resolution and fps
        # This formula accounts for both pixel count and frame rate
        # Using bits-per-pixel approach for H.264 encoding
        pixels_per_second = width * height * fps

        # Different quality factors based on resolution
        if width >= 1920 and height >= 1080:  # Full HD
            # Higher quality for HD content: ~0.1 bits per pixel
            bits_per_pixel = 0.1
        elif width >= 1280 and height >= 720:  # HD
            # Medium-high quality: ~0.08 bits per pixel
            bits_per_pixel = 0.08
        elif width >= 854 and height >= 480:  # SD
            # Medium quality: ~0.06 bits per pixel
            bits_per_pixel = 0.06
        else:  # Lower quality
            # Lower quality for smaller video: ~0.05 bits per pixel
            bits_per_pixel = 0.05

        # Calculate bitrate in kbps
        estimated_bitrate = int(pixels_per_second * bits_per_pixel / 1000)

        # Set reasonable min/max boundaries
        min_bitrate = 100  # Minimum acceptable bitrate
        max_bitrate = 5000  # Maximum reasonable bitrate for WebRTC

        bitrate = max(min_bitrate, min(estimated_bitrate, max_bitrate))

        logger.info(f"Detected video properties: {width}x{height} at {fps}fps")
        logger.info(
            f"Calculated bitrate: {bitrate} kbps (based on {bits_per_pixel} bits/pixel)"
        )

        return {"width": width, "height": height, "fps": fps, "bitrate": bitrate}
    except asyncio.TimeoutError:
        logger.error("Timeout while waiting for video frame")
        return default_properties
    except Exception as e:
        logger.error(f"Error detecting video properties: {e}")
        return default_properties
    finally:
        # Clean up only if we created our own buffered track
        if own_buffered_track and buffered_track:
            try:
                # Clean up the buffered track but don't stop the original track
                buffered_track._buffered_frames = []
                buffered_track._ended = True
            except Exception as e:
                logger.error(f"Error cleaning up buffered track: {e}")


def _normalize_audio_format(
    pcm: PcmData, target_sample_rate: int, target_format: AudioFormatType
) -> PcmData:
    """
    Helper function to normalize audio to target sample rate and format.

    Args:
        pcm: Input audio data
        target_sample_rate: Target sample rate
        target_format: Target format (AudioFormat.S16 or AudioFormat.F32)

    Returns:
        PcmData with target sample rate and format
    """
    # Validate format
    AudioFormat.validate(target_format)
    # Resample if needed
    if pcm.sample_rate != target_sample_rate:
        pcm = pcm.resample(target_sample_rate)

    # Convert format if needed
    if target_format == "f32" and pcm.format != "f32":
        pcm = pcm.to_float32()
    elif target_format == "s16" and pcm.format != "s16":
        pcm = pcm.to_int16()

    return pcm


class AudioTrackHandler:
    """
    A helper to receive raw PCM data from an aiortc AudioStreamTrack
    and feed it into the provided callback.
    """

    def __init__(
        self, track: MediaStreamTrack, on_audio_frame: Callable[[PcmData], Any]
    ):
        """
        :param track: The incoming audio track (from `pc.on("track")`).
        :param on_audio_frame: A callback function that will receive
                               the PCM data as a NumPy array (int16).
        """
        self.track = track
        self._on_audio_frame = on_audio_frame
        self._task = None
        self._stopped = False

    async def start(self):
        """
        Start reading frames from the track in a background task.
        """
        if self._task is None:
            self._task = asyncio.create_task(self._run_track())

    async def stop(self):
        """
        Stop reading frames and clean up.
        """
        self._stopped = True
        if self._task:
            self._task.cancel()
            try:
                await self._task
            except asyncio.CancelledError:
                pass
            self._task = None

    async def _run_track(self):
        """
        Internal coroutine that continuously pulls frames from the track.
        """

        while not self._stopped:
            try:
                frame = await self.track.recv()
            except asyncio.CancelledError:
                # Task was cancelled, safe to exit
                break
            except MediaStreamError:
                # Error with the media stream, possibly EOF
                break
            except Exception as e:
                logger.error(f"Error receiving audio frame: {e}")
                break

            if not isinstance(frame, av.AudioFrame):
                raise TypeError("Audio frame not received")

            if frame.sample_rate != 48000:
                raise TypeError("only 48000 sample rate supported")

            try:
                pcm_ndarray = frame.to_ndarray()
            except Exception as plane_error:
                logger.error(
                    f"Error converting audio frame to ndarray: {plane_error}, dropping frame"
                )
                break

            # Handle stereo to mono conversion
            if len(frame.layout.channels) > 1:
                try:
                    # Reshape to separate stereo channels: [L, R, L, R, ...] -> [[L, R], [L, R], ...]
                    # This assumes the data is interleaved stereo
                    audio_stereo = pcm_ndarray.reshape(-1, len(frame.layout.channels))
                    # Take the mean across channels to convert to mono
                    pcm_ndarray = audio_stereo.mean(axis=1).astype(np.int16)
                except ValueError as e:
                    logger.error(
                        f"Error reshaping stereo audio: {e}. "
                        f"Original shape: {pcm_ndarray.shape}, channels: {len(frame.layout.channels)}"
                    )
                    break

            # Extract timestamp information from the frame
            pts = getattr(frame, "pts", None)
            dts = getattr(frame, "dts", None)
            time_base = None

            # Convert time_base to float if available
            if hasattr(frame, "time_base") and frame.time_base is not None:
                try:
                    # time_base is typically a fractions.Fraction, convert to float
                    time_base = float(frame.time_base)
                except (TypeError, ValueError):
                    logger.warning(
                        f"Could not convert time_base to float: {frame.time_base}"
                    )
                    time_base = None

            self._on_audio_frame(
                PcmData(
                    sample_rate=48_000,
                    format="s16",
                    samples=pcm_ndarray,
                    pts=pts,
                    dts=dts,
                    time_base=time_base,
                )
            )
