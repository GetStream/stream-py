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
    Audio stream track that accepts PcmData objects directly from a queue.

    Works with PcmData objects instead of raw bytes, avoiding format conversion issues.

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
        max_queue_size: int = 100,
    ):
        """
        Initialize an AudioStreamTrack that accepts PcmData objects.

        Args:
            sample_rate: Target sample rate in Hz (default: 48000)
            channels: Number of channels - 1=mono, 2=stereo (default: 1)
            format: Audio format - "s16" or "f32" (default: "s16")
            max_queue_size: Maximum number of PcmData objects in queue (default: 100)
        """
        super().__init__()
        self.sample_rate = sample_rate
        self.channels = channels
        self.format = format
        self.max_queue_size = max_queue_size

        logger.debug(
            "Initialized AudioStreamTrack",
            extra={
                "sample_rate": sample_rate,
                "channels": channels,
                "format": format,
                "max_queue_size": max_queue_size,
            },
        )

        # Create async queue for PcmData objects
        self._queue = asyncio.Queue()
        self._start = None
        self._timestamp = None

        # Buffer for chunks smaller than 20ms
        self._buffer = None

    async def write(self, pcm: PcmData):
        """
        Add PcmData to the queue.

        The PcmData will be automatically resampled/converted to match
        the track's configured sample_rate, channels, and format.

        Args:
            pcm: PcmData object with audio data
        """
        # Check if queue is getting too large and trim if necessary
        if self._queue.qsize() >= self.max_queue_size:
            dropped_items = 0
            while self._queue.qsize() >= self.max_queue_size:
                try:
                    self._queue.get_nowait()
                    self._queue.task_done()
                    dropped_items += 1
                except asyncio.QueueEmpty:
                    break

            logger.warning(
                "Audio queue overflow, dropped items",
                extra={
                    "dropped_items": dropped_items,
                    "queue_size": self._queue.qsize(),
                },
            )

        await self._queue.put(pcm)
        logger.debug(
            "Added PcmData to queue",
            extra={
                "pcm_samples": len(pcm.samples)
                if pcm.samples.ndim == 1
                else pcm.samples.shape,
                "pcm_sample_rate": pcm.sample_rate,
                "pcm_channels": pcm.channels,
                "queue_size": self._queue.qsize(),
            },
        )

    async def flush(self) -> None:
        """
        Clear any pending audio from the queue and buffer.
        Playback stops immediately.
        """
        cleared = 0
        while not self._queue.empty():
            try:
                self._queue.get_nowait()
                self._queue.task_done()
                cleared += 1
            except asyncio.QueueEmpty:
                break

        self._buffer = None
        logger.debug("Flushed audio queue", extra={"cleared_items": cleared})

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
        else:
            self._timestamp += samples_per_frame
            start_ts = self._start or time.time()
            wait = start_ts + (self._timestamp / self.sample_rate) - time.time()
            if wait > 0:
                await asyncio.sleep(wait)

        # Get or accumulate PcmData to fill a 20ms frame
        pcm_for_frame = await self._get_pcm_for_frame(samples_per_frame)

        # Create AudioFrame
        # Determine layout and format
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
        if pcm_for_frame is not None:
            audio_bytes = pcm_for_frame.to_bytes()

            # Write to the single plane (packed format has 1 plane)
            if len(audio_bytes) >= frame.planes[0].buffer_size:
                frame.planes[0].update(audio_bytes[: frame.planes[0].buffer_size])
            else:
                # Pad with silence if not enough data
                padding = bytes(frame.planes[0].buffer_size - len(audio_bytes))
                frame.planes[0].update(audio_bytes + padding)
        else:
            # No data available, return silence
            for plane in frame.planes:
                plane.update(bytes(plane.buffer_size))

        # Set frame properties
        frame.pts = self._timestamp
        frame.sample_rate = self.sample_rate
        frame.time_base = fractions.Fraction(1, self.sample_rate)

        return frame

    async def _get_pcm_for_frame(self, samples_needed: int) -> PcmData | None:
        """
        Get or accumulate PcmData to fill exactly samples_needed samples.

        This method handles:
        - Buffering partial chunks
        - Resampling to target sample rate
        - Converting to target channels
        - Converting to target format
        - Chunking to exact frame size

        Args:
            samples_needed: Number of samples needed for the frame

        Returns:
            PcmData with exactly samples_needed samples, or None if no data available
        """
        # Start with buffered data if any
        if self._buffer is not None:
            pcm_accumulated = self._buffer
            self._buffer = None
        else:
            pcm_accumulated = None

        # Try to get data from queue
        try:
            # Don't wait too long - if no data, return silence
            while True:
                # Check if we have enough samples
                if pcm_accumulated is not None:
                    current_samples = (
                        len(pcm_accumulated.samples)
                        if pcm_accumulated.samples.ndim == 1
                        else pcm_accumulated.samples.shape[1]
                    )
                    if current_samples >= samples_needed:
                        break

                # Try to get more data
                if self._queue.empty():
                    # No more data available
                    break

                pcm_chunk = await asyncio.wait_for(self._queue.get(), timeout=0.01)
                self._queue.task_done()

                # Resample/convert to target format
                pcm_chunk = self._normalize_pcm(pcm_chunk)

                # Accumulate
                if pcm_accumulated is None:
                    pcm_accumulated = pcm_chunk
                else:
                    pcm_accumulated = pcm_accumulated.append(pcm_chunk)

        except asyncio.TimeoutError:
            pass

        # If no data at all, return None (will produce silence)
        if pcm_accumulated is None:
            return None

        # Get the number of samples we have
        current_samples = (
            len(pcm_accumulated.samples)
            if pcm_accumulated.samples.ndim == 1
            else pcm_accumulated.samples.shape[1]
        )

        # If we have exactly the right amount, return it
        if current_samples == samples_needed:
            return pcm_accumulated

        # If we have more than needed, split it
        if current_samples > samples_needed:
            # Calculate duration needed in seconds
            duration_needed_s = samples_needed / self.sample_rate

            # Use head() to get exactly what we need
            pcm_for_frame = pcm_accumulated.head(
                duration_s=duration_needed_s, pad=False, pad_at="end"
            )

            # Calculate what's left in seconds
            duration_used_s = (
                len(pcm_for_frame.samples)
                if pcm_for_frame.samples.ndim == 1
                else pcm_for_frame.samples.shape[1]
            ) / self.sample_rate

            # Buffer the rest
            self._buffer = pcm_accumulated.tail(
                duration_s=pcm_accumulated.duration - duration_used_s,
                pad=False,
                pad_at="start",
            )

            return pcm_for_frame

        # If we have less than needed, return what we have (will be padded with silence)
        return pcm_accumulated

    def _normalize_pcm(self, pcm: PcmData) -> PcmData:
        """
        Normalize PcmData to match the track's target format.

        Args:
            pcm: Input PcmData

        Returns:
            PcmData resampled/converted to target sample_rate, channels, and format
        """
        # Resample to target sample rate and channels if needed
        if pcm.sample_rate != self.sample_rate or pcm.channels != self.channels:
            pcm = pcm.resample(self.sample_rate, target_channels=self.channels)

        # Convert format if needed
        if self.format == "s16" and pcm.format != "s16":
            pcm = pcm.to_int16()
        elif self.format == "f32" and pcm.format != "f32":
            pcm = pcm.to_float32()

        return pcm
