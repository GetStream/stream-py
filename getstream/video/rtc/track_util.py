import asyncio
import io
import wave

import av
import numpy as np
import re
from typing import (
    Dict,
    Any,
    NamedTuple,
    Callable,
    Optional,
    Union,
    Iterator,
    AsyncIterator,
)

import logging
import aiortc
from aiortc import MediaStreamTrack
from aiortc.mediastreams import MediaStreamError
from numpy.typing import NDArray

logger = logging.getLogger(__name__)


class PcmData(NamedTuple):
    """
    A named tuple representing PCM audio data.

    Attributes:
        format: The format of the audio data.
        sample_rate: The sample rate of the audio data.
        samples: The audio samples as a numpy array.
        pts: The presentation timestamp of the audio data.
        dts: The decode timestamp of the audio data.
        time_base: The time base for converting timestamps to seconds.
    """

    format: str
    sample_rate: int
    samples: NDArray = np.array([], dtype=np.int16)
    pts: Optional[int] = None  # Presentation timestamp
    dts: Optional[int] = None  # Decode timestamp
    time_base: Optional[float] = None  # Time base for converting timestamps to seconds
    channels: int = 1  # Number of channels (1=mono, 2=stereo)

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
        # The samples field contains a numpy array of audio samples
        # For s16 format, each element in the array is one sample (int16)
        # For f32 format, each element in the array is one sample (float32)

        if isinstance(self.samples, np.ndarray):
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
        elif isinstance(self.samples, bytes):
            # If samples is bytes, calculate based on format
            if self.format == "s16":
                # For s16 format, each sample is 2 bytes (16 bits)
                # For multi-channel, divide by channels to get sample count
                num_samples = len(self.samples) // (
                    2 * (self.channels if self.channels else 1)
                )
            elif self.format == "f32":
                # For f32 format, each sample is 4 bytes (32 bits)
                num_samples = len(self.samples) // (
                    4 * (self.channels if self.channels else 1)
                )
            else:
                # Default assumption for other formats (treat as raw bytes)
                num_samples = len(self.samples)
        else:
            # Fallback: try to get length
            try:
                num_samples = len(self.samples)
            except TypeError:
                logger.warning(
                    f"Cannot determine sample count for type {type(self.samples)}"
                )
                return 0.0

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
        format: str = "s16",
        channels: int = 1,
    ) -> "PcmData":
        """Build from raw PCM bytes (interleaved).

        Example:
        >>> import numpy as np
        >>> b = np.array([1, -1, 2, -2], dtype=np.int16).tobytes()
        >>> pcm = PcmData.from_bytes(b, sample_rate=16000, format="s16", channels=2)
        >>> pcm.samples.shape[0]  # channels-first
        2
        """
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
    def from_data(
        cls,
        data: Union[bytes, bytearray, memoryview, NDArray],
        sample_rate: int = 16000,
        format: str = "s16",
        channels: int = 1,
    ) -> "PcmData":
        """Build from bytes or numpy arrays.

        Example:
        >>> import numpy as np
        >>> PcmData.from_data(np.array([1, 2], np.int16), sample_rate=16000, format="s16", channels=1).channels
        1
        """
        if isinstance(data, (bytes, bytearray, memoryview)):
            return cls.from_bytes(
                bytes(data), sample_rate=sample_rate, format=format, channels=channels
            )

        if isinstance(data, np.ndarray):
            arr = data
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

        # Unsupported type
        raise TypeError(f"Unsupported data type for PcmData: {type(data)}")

    def resample(
        self,
        target_sample_rate: int,
        target_channels: Optional[int] = None,
        resampler: Optional[Any] = None,
    ) -> "PcmData":
        """Resample to target sample rate/channels.

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

        # Prepare ndarray shape for AV input frame.
        # Use planar input (s16p) with shape (channels, samples).
        in_layout = "mono" if self.channels == 1 else "stereo"
        cmaj = self.samples
        if isinstance(cmaj, np.ndarray):
            if cmaj.ndim == 1:
                # (samples,) -> (channels, samples)
                if self.channels > 1:
                    cmaj = np.tile(cmaj, (self.channels, 1))
                else:
                    cmaj = cmaj.reshape(1, -1)
            elif cmaj.ndim == 2:
                # Normalize to (channels, samples)
                ch = self.channels if self.channels else 1
                if cmaj.shape[0] == ch:
                    # Already (channels, samples)
                    pass
                elif cmaj.shape[1] == ch:
                    # (samples, channels) -> transpose
                    cmaj = cmaj.T
                else:
                    # Ambiguous - assume larger dim is samples
                    if cmaj.shape[1] > cmaj.shape[0]:
                        # Likely (channels, samples)
                        pass
                    else:
                        # Likely (samples, channels)
                        cmaj = cmaj.T
            cmaj = np.ascontiguousarray(cmaj)
        frame = av.AudioFrame.from_ndarray(cmaj, format="s16p", layout=in_layout)
        frame.sample_rate = self.sample_rate

        # Use provided resampler or create a new one
        if resampler is None:
            # Create new resampler for one-off use
            out_layout = "mono" if target_channels == 1 else "stereo"
            resampler = av.AudioResampler(
                format="s16", layout=out_layout, rate=target_sample_rate
            )

        # Resample the frame
        resampled_frames = resampler.resample(frame)
        if resampled_frames:
            resampled_frame = resampled_frames[0]
            # PyAV's to_ndarray() for packed format returns flattened interleaved data
            # For stereo s16 (packed), it returns shape (1, num_values) where num_values = samples * channels
            raw_array = resampled_frame.to_ndarray()
            num_frames = resampled_frame.samples  # Actual number of sample frames

            # Normalize output to (channels, samples) format
            ch = int(target_channels)

            # Handle PyAV's packed format quirk: returns (1, num_values) for stereo
            if raw_array.ndim == 2 and raw_array.shape[0] == 1 and ch > 1:
                # Flatten and deinterleave packed stereo data
                # Shape (1, 32000) -> (32000,) -> deinterleave to (2, 16000)
                flat = raw_array.reshape(-1)
                if len(flat) == num_frames * ch:
                    # Deinterleave: [L0,R0,L1,R1,...] -> [[L0,L1,...], [R0,R1,...]]
                    resampled_samples = flat.reshape(-1, ch).T
                else:
                    logger.warning(
                        "Unexpected array size %d for %d frames x %d channels",
                        len(flat),
                        num_frames,
                        ch,
                    )
                    resampled_samples = flat.reshape(ch, -1)
            elif raw_array.ndim == 2:
                # Standard case: (samples, channels) or already (channels, samples)
                if raw_array.shape[1] == ch:
                    # (samples, channels) -> transpose to (channels, samples)
                    resampled_samples = raw_array.T
                elif raw_array.shape[0] == ch:
                    # Already (channels, samples)
                    resampled_samples = raw_array
                else:
                    # Ambiguous - assume time-major
                    resampled_samples = raw_array.T
            elif raw_array.ndim == 1:
                # 1D output (mono)
                if ch == 1:
                    # Keep as 1D for mono
                    resampled_samples = raw_array
                elif ch > 1:
                    # Shouldn't happen if we requested stereo, but handle it
                    logger.warning(
                        "Got 1D array but requested %d channels, duplicating", ch
                    )
                    resampled_samples = np.tile(raw_array, (ch, 1))
                else:
                    resampled_samples = raw_array
            else:
                # Unexpected dimensionality
                logger.warning(
                    "Unexpected ndim %d from PyAV, reshaping", raw_array.ndim
                )
                resampled_samples = raw_array.reshape(ch, -1)

            # Flatten mono arrays to 1D for consistency
            if (
                ch == 1
                and isinstance(resampled_samples, np.ndarray)
                and resampled_samples.ndim > 1
            ):
                resampled_samples = resampled_samples.flatten()

            # Ensure int16 dtype for s16
            if (
                isinstance(resampled_samples, np.ndarray)
                and resampled_samples.dtype != np.int16
            ):
                resampled_samples = resampled_samples.astype(np.int16)

            return PcmData(
                samples=resampled_samples,
                sample_rate=target_sample_rate,
                format="s16",
                pts=self.pts,
                dts=self.dts,
                time_base=self.time_base,
                channels=target_channels,
            )
        else:
            # If resampling failed, return original data
            return self

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
        try:
            return bytes(arr)
        except Exception:
            logger.warning("Cannot convert samples to bytes; returning empty")
            return b""

    def to_wav_bytes(self) -> bytes:
        """Return WAV bytes (header + frames).

        Example:
        >>> import numpy as np
        >>> pcm = PcmData(samples=np.array([0, 0], np.int16), sample_rate=16000, format="s16", channels=1)
        >>> with open("out.wav", "wb") as f:  # write to disk
        ...     _ = f.write(pcm.to_wav_bytes())
        """
        # Ensure s16 frames
        if self.format != "s16":
            arr = self.samples
            if isinstance(arr, np.ndarray):
                if arr.dtype != np.int16:
                    # Convert floats to int16 range
                    if arr.dtype != np.float32:
                        arr = arr.astype(np.float32)
                    arr = (np.clip(arr, -1.0, 1.0) * 32767.0).astype(np.int16)
                frames = PcmData(
                    samples=arr,
                    sample_rate=self.sample_rate,
                    format="s16",
                    pts=self.pts,
                    dts=self.dts,
                    time_base=self.time_base,
                    channels=self.channels,
                ).to_bytes()
            else:
                frames = self.to_bytes()
            width = 2
        else:
            frames = self.to_bytes()
            width = 2

        buf = io.BytesIO()
        with wave.open(buf, "wb") as wf:
            wf.setnchannels(self.channels or 1)
            wf.setsampwidth(width)
            wf.setframerate(self.sample_rate)
            wf.writeframes(frames)
        return buf.getvalue()

    def to_float32(self) -> "PcmData":
        """Convert samples to float32 in [-1, 1].

        Example:
        >>> import numpy as np
        >>> pcm = PcmData(samples=np.array([0, 1], np.int16), sample_rate=16000, format="s16", channels=1)
        >>> pcm.to_float32().samples.dtype == np.float32
        True
        """
        arr = self.samples

        # Normalize to a numpy array for conversion
        if not isinstance(arr, np.ndarray):
            try:
                # Round-trip through bytes to reconstruct canonical ndarray shape
                arr = PcmData.from_bytes(
                    self.to_bytes(),
                    sample_rate=self.sample_rate,
                    format=self.format,
                    channels=self.channels,
                ).samples
            except Exception:
                # Fallback to from_data for robustness
                arr = PcmData.from_data(
                    self.samples,
                    sample_rate=self.sample_rate,
                    format=self.format,
                    channels=self.channels,
                ).samples

        # Convert to float32 and scale if needed
        fmt = (self.format or "").lower()
        if fmt in ("s16", "int16") or (
            isinstance(arr, np.ndarray) and arr.dtype == np.int16
        ):
            arr_f32 = arr.astype(np.float32) / 32768.0
        else:
            # Ensure dtype float32; values assumed already in [-1, 1]
            arr_f32 = arr.astype(np.float32, copy=False)

        return PcmData(
            samples=arr_f32,
            sample_rate=self.sample_rate,
            format="f32",
            pts=self.pts,
            dts=self.dts,
            time_base=self.time_base,
            channels=self.channels,
        )

    def append(self, other: "PcmData") -> "PcmData":
        """Append another chunk after adjusting it to match self.

        Example:
        >>> import numpy as np
        >>> a = PcmData(samples=np.array([1, 2], np.int16), sample_rate=16000, format="s16", channels=1)
        >>> b = PcmData(samples=np.array([3, 4], np.int16), sample_rate=16000, format="s16", channels=1)
        >>> a.append(b).samples.tolist()
        [1, 2, 3, 4]
        """

        # Early exits for empty cases
        def _is_empty(arr: Any) -> bool:
            try:
                return isinstance(arr, np.ndarray) and arr.size == 0
            except Exception:
                return False

        # Normalize numpy arrays from bytes-like if needed
        def _ensure_ndarray(pcm: "PcmData") -> np.ndarray:
            if isinstance(pcm.samples, np.ndarray):
                return pcm.samples
            return PcmData.from_bytes(
                pcm.to_bytes(),
                sample_rate=pcm.sample_rate,
                format=pcm.format,
                channels=pcm.channels,
            ).samples

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
            # Ensure int16 dtype and mark as s16
            arr = _ensure_ndarray(other_adj)
            if arr.dtype != np.int16:
                if other_adj.format == "f32":
                    arr = (np.clip(arr.astype(np.float32), -1.0, 1.0) * 32767.0).astype(
                        np.int16
                    )
                else:
                    arr = arr.astype(np.int16)
            other_adj = PcmData(
                samples=arr,
                sample_rate=other_adj.sample_rate,
                format="s16",
                pts=other_adj.pts,
                dts=other_adj.dts,
                time_base=other_adj.time_base,
                channels=other_adj.channels,
            )
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

        # If either is empty, return the other while preserving self's metadata
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
            return PcmData(
                samples=other_arr,
                sample_rate=self.sample_rate,
                format=self.format,
                pts=self.pts,
                dts=self.dts,
                time_base=self.time_base,
                channels=self.channels,
            )
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
            return PcmData(
                samples=out,
                sample_rate=self.sample_rate,
                format=self.format,
                pts=self.pts,
                dts=self.dts,
                time_base=self.time_base,
                channels=self.channels,
            )
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

            return PcmData(
                samples=out,
                sample_rate=self.sample_rate,
                format=self.format,
                pts=self.pts,
                dts=self.dts,
                time_base=self.time_base,
                channels=self.channels,
            )

    @classmethod
    def from_response(
        cls,
        response: Any,
        *,
        sample_rate: int = 16000,
        channels: int = 1,
        format: str = "s16",
    ) -> Union["PcmData", Iterator["PcmData"], AsyncIterator["PcmData"]]:
        """Normalize provider response to PcmData or iterators of it.

        Example:
        >>> PcmData.from_response(bytes([0, 0]), sample_rate=16000, format="s16").sample_rate
        16000
        """

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
                width = 2 if format == "s16" else 4 if format == "f32" else 2
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
                    aligned = (len(buf) // frame_width) * frame_width
                    if aligned:
                        chunk = bytes(buf[:aligned])
                        del buf[:aligned]
                        yield cls.from_bytes(
                            chunk,
                            sample_rate=sample_rate,
                            channels=channels,
                            format=format,
                        )
                # pad remainder, if any
                if buf:
                    pad_len = (-len(buf)) % frame_width
                    if pad_len:
                        buf.extend(b"\x00" * pad_len)
                    yield cls.from_bytes(
                        bytes(buf),
                        sample_rate=sample_rate,
                        channels=channels,
                        format=format,
                    )

            return _agen()

        # Sync iterator (but skip treating bytes as iterable of ints)
        if hasattr(response, "__iter__") and not isinstance(
            response, (str, bytes, bytearray, memoryview)
        ):

            def _gen():
                width = 2 if format == "s16" else 4 if format == "f32" else 2
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
                    aligned = (len(buf) // frame_width) * frame_width
                    if aligned:
                        chunk = bytes(buf[:aligned])
                        del buf[:aligned]
                        yield cls.from_bytes(
                            chunk,
                            sample_rate=sample_rate,
                            channels=channels,
                            format=format,
                        )
                if buf:
                    pad_len = (-len(buf)) % frame_width
                    if pad_len:
                        buf.extend(b"\x00" * pad_len)
                    yield cls.from_bytes(
                        bytes(buf),
                        sample_rate=sample_rate,
                        channels=channels,
                        format=format,
                    )

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
        if reference_ice:
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
    """A wrapper for MediaStreamTrack that buffers one peeked frame."""

    def __init__(self, track):
        super().__init__()
        self._track = track
        self._buffered_frames = []  # Store multiple frames
        self._kind = track.kind
        self._id = track.id
        self._ended = False

    @property
    def kind(self):
        return self._kind

    @property
    def id(self):
        return self._id

    @property
    def readyState(self):
        return "ended" if self._ended else self._track.readyState

    async def recv(self):
        """Returns the next buffered frame if available, otherwise gets a new frame from the track."""
        if self._ended:
            raise MediaStreamError("Track is ended")

        if self._buffered_frames:
            # Return the oldest buffered frame (FIFO order)
            return self._buffered_frames.pop(0)

        try:
            return await self._track.recv()
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
                    self._track.stop_audio()
                except Exception as e:
                    logger.error(f"Error stopping track: {e}")


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
                    samples=pcm_ndarray,
                    format="s16",
                    pts=pts,
                    dts=dts,
                    time_base=time_base,
                )
            )
