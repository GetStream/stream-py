import asyncio
import fractions
import logging
import time
from collections import deque

import aiortc
import av
import numpy as np

from .track_util import AudioFormat, AudioFormatType, FrameResampler, PcmData

logger = logging.getLogger(__name__)


class AudioStreamTrack(aiortc.mediastreams.MediaStreamTrack):
    """aiortc audio track that streams buffered PCM into a WebRTC call.

    `write()` accepts PcmData at any sample rate, channel layout, or format, and converts it to fixed 20ms packed-s16 frames at the track's output
    rate/layout and queues them (dropping the oldest once the queue exceeds
    audio_buffer_size_ms).

    `recv()` paces the queue out in real time via _FramePacer,
    handing back one frame per call with its pts stamped, and synthesizes silence
    when the queue is empty so the RTP timeline never stalls.

    `flush()` clears the queue to support interruption/barge-in.
    """

    kind = "audio"

    def __init__(
        self,
        sample_rate: int = 48000,  # rate of emitted frames; 48kHz matches Opus (avoids a re-resample)
        channels: int = 1,  # output channel count (1=mono, 2=stereo)
        format: AudioFormatType = AudioFormat.S16,  # output sample format; must be s16 (aiortc's Opus encoder requirement)
        audio_buffer_size_ms: int = 30000,  # max audio to hold before dropping oldest
    ):
        super().__init__()
        if format != AudioFormat.S16:
            raise ValueError(
                f"AudioStreamTrack output format must be 's16', got {format!r}; "
                "aiortc's Opus encoder only accepts s16 frames."
            )
        self.sample_rate = sample_rate
        self.channels = channels
        self.format = format
        self.audio_buffer_size_ms = audio_buffer_size_ms

        self._frame_buffer: deque[av.AudioFrame] = deque()
        # Running per-channel sample total, to enforce the size cap cheaply.
        self._buffered_samples = 0
        # Serializes buffer mutation between write() and recv().
        self._frame_lock = asyncio.Lock()

        self._layout = "stereo" if channels == 2 else "mono"
        # Samples-per-channel in one 20ms frame (e.g. 0.02 * 48000 = 960).
        self._samples_per_frame = int(aiortc.mediastreams.AUDIO_PTIME * sample_rate)
        # Cap in per-channel samples; beyond this, the oldest frames are dropped.
        self._max_samples = int((audio_buffer_size_ms / 1000) * sample_rate)
        # Pre-built zeros reused to synthesize a silence frame on starvation.
        self._silence = np.zeros(
            (1, self._samples_per_frame * channels), dtype=np.int16
        )

        # Resampling and pacing state live in their own helpers; the track only
        # calls their methods.
        self._resampler = FrameResampler(
            rate=sample_rate,
            layout=self._layout,
            format=format,
            frame_size=self._samples_per_frame,
        )
        self._pacer = _FramePacer(sample_rate, self._samples_per_frame)

    async def write(self, pcm: PcmData, final: bool = False) -> None:
        """Write PCM data to the track.

        Under the hood, it resamples to fixed 20ms frames and buffers them.
        When final is True, drain the resampler's tail so the utterance plays out.

        Args:
            pcm: PCM data to write
            final: if True, drain the resampler's tail and add it to the buffer
                (e.g. on end-of-utterance event).
        """
        # Zero or more finished 20ms frames (empty while swr is still buffering).
        frames = self._resampler.resample(pcm, flush=final)
        if not frames:
            return

        async with self._frame_lock:
            for frame in frames:
                self._frame_buffer.append(frame)
                self._buffered_samples += frame.samples

            # Bound latency/memory: if the producer outran the consumer, drop the
            # oldest frames until back under the cap.
            while self._buffered_samples > self._max_samples and self._frame_buffer:
                self._buffered_samples -= self._frame_buffer.popleft().samples

    async def flush(self) -> None:
        """Drop pending frames and reset the resampler (interruption)."""
        async with self._frame_lock:
            # Cut off queued playback (barge-in) and reset the resampler so no
            # samples bleed into the next utterance.
            self._frame_buffer.clear()
            self._buffered_samples = 0
            self._resampler.flush()

    async def recv(self) -> av.AudioFrame:
        """Return the next 20ms frame, synthesizing silence when starved."""
        # aiortc calls recv() in a loop; once the track is stopped, signal EOF.
        if self.readyState != "live":
            raise aiortc.mediastreams.MediaStreamError

        # Block until this frame is due, and get the pts to stamp on it.
        pts = await self._pacer.next_pts()

        async with self._frame_lock:
            if self._frame_buffer:
                # Normal path: hand out the next ready frame.
                frame = self._frame_buffer.popleft()
                self._buffered_samples -= frame.samples
            else:
                # Starved (gap between utterances): emit a silence frame so the RTP
                # timeline stays continuous instead of stalling.
                frame = av.AudioFrame.from_ndarray(
                    self._silence, format="s16", layout=self._layout
                )

        # A flushed tail can be shorter than a full frame; pad it with trailing
        # silence so every emitted frame fills its fixed-rate pts slot.
        if frame.samples < self._samples_per_frame:
            frame = self._pad_to_full_frame(frame)

        # Stamp the frame's timing so the encoder/RTP sender place it correctly.
        frame.pts = pts
        frame.sample_rate = self.sample_rate
        frame.time_base = fractions.Fraction(1, self.sample_rate)
        return frame

    def _pad_to_full_frame(self, frame: av.AudioFrame) -> av.AudioFrame:
        """Pad a short (flushed-tail) frame up to a full frame with trailing silence."""
        data = frame.to_ndarray()
        pad = self._samples_per_frame * self.channels - data.shape[1]
        padded = np.pad(data, ((0, 0), (0, pad)))
        return av.AudioFrame.from_ndarray(padded, format="s16", layout=self._layout)


class _FramePacer:
    """Real-time clock for fixed-size frames.

    aiortc sends whatever recv() returns immediately, so recv() must block until each
    frame is due. next_pts() sleeps the right amount and returns the pts to stamp.
    """

    def __init__(self, sample_rate: int, samples_per_frame: int):
        self._sample_rate = sample_rate
        self._samples_per_frame = samples_per_frame
        # Monotonic clock anchor and sample cursor (= next pts); None until start.
        self._start: float | None = None
        self._ts: int | None = None

    async def next_pts(self) -> int:
        if self._ts is None:
            # First frame: anchor the clock and emit without waiting.
            self._start = time.monotonic()
            self._ts = 0
        else:
            # Advance one frame and sleep until that time. Anchoring to _start
            # (not the previous frame) keeps drift from accumulating. monotonic()
            # is used so a wall-clock step (NTP, VM migration) can't stall pacing.
            self._ts += self._samples_per_frame
            start = self._start or time.monotonic()
            wait = start + self._ts / self._sample_rate - time.monotonic()
            if wait > 0:
                await asyncio.sleep(wait)
        return self._ts
