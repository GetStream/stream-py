"""Duck-typed media helpers used by the Rust-backed RTC stack.

Tracks expose the historic aiortc `recv()` / `readyState` / `stop()` surface so
`add_tracks` and `AudioStreamTrack` callers stay unchanged.
"""

from __future__ import annotations

import asyncio
import logging
import uuid
from typing import Any, Optional

import av
import numpy as np

logger = logging.getLogger(__name__)

try:
    from aiortc.mediastreams import MediaStreamError
except ImportError:

    class MediaStreamError(Exception):
        """Raised when a media track is ended or recv() fails."""


AUDIO_PTIME = 0.020


class MediaStreamTrack:
    """Minimal MediaStreamTrack stand-in (kind, id, readyState, stop, recv)."""

    kind = "unknown"

    def __init__(self) -> None:
        self._id = str(uuid.uuid4())
        self._readyState = "live"

    @property
    def id(self) -> str:
        return self._id

    @property
    def readyState(self) -> str:
        return self._readyState

    def stop(self) -> None:
        self._readyState = "ended"

    async def recv(self):
        raise MediaStreamError("Track has no recv implementation")


class QueueTrack(MediaStreamTrack):
    """A track that yields frames from an asyncio queue (MediaRelay stand-in)."""

    def __init__(self, kind: str, track_id: str, queue: asyncio.Queue) -> None:
        super().__init__()
        self.kind = kind
        self._id = track_id
        self._queue = queue

    async def recv(self):
        if self.readyState != "live":
            raise MediaStreamError("Track is ended")
        frame = await self._queue.get()
        if frame is None:
            self.stop()
            raise MediaStreamError("Track is ended")
        return frame


class FrameRelay:
    """Fan-out decoded frames to one or more QueueTrack subscribers."""

    def __init__(self, kind: str, track_id: str) -> None:
        self.kind = kind
        self.track_id = track_id
        self._queues: list[asyncio.Queue] = []
        self._ended = False

    def subscribe(self, maxsize: int = 32) -> QueueTrack:
        queue: asyncio.Queue = asyncio.Queue(maxsize=maxsize)
        self._queues.append(queue)
        return QueueTrack(self.kind, self.track_id, queue)

    async def push(self, frame: Any) -> None:
        if self._ended:
            return
        for queue in list(self._queues):
            if queue.full():
                try:
                    queue.get_nowait()
                except asyncio.QueueEmpty:
                    pass
            try:
                queue.put_nowait(frame)
            except asyncio.QueueFull:
                pass

    def close(self) -> None:
        self._ended = True
        for queue in list(self._queues):
            try:
                queue.put_nowait(None)
            except asyncio.QueueFull:
                pass


def pcm_bytes_to_pcmdata(
    samples: bytes,
    sample_rate: int,
    channels: int,
    participant: Any = None,
):
    from getstream.video.rtc.track_util import AudioFormat, PcmData

    array = np.frombuffer(samples, dtype=np.int16)
    if channels > 1:
        array = array.reshape(-1, channels).T
    return PcmData(
        samples=array,
        sample_rate=sample_rate,
        format=AudioFormat.S16,
        channels=channels,
        participant=participant,
    )


def pcm_bytes_to_av_frame(
    samples: bytes, sample_rate: int, channels: int
) -> av.AudioFrame:
    array = np.frombuffer(samples, dtype=np.int16)
    layout = "stereo" if channels == 2 else "mono"
    if channels == 1:
        ndarray = array.reshape(1, -1)
    else:
        ndarray = array.reshape(-1, channels).T
    frame = av.AudioFrame.from_ndarray(ndarray, format="s16", layout=layout)
    frame.sample_rate = sample_rate
    return frame


def av_audio_to_pcm_bytes(frame: av.AudioFrame) -> tuple[bytes, int, int]:
    from getstream.video.rtc.track_util import PcmData

    pcm = PcmData.from_av_frame(frame)
    samples = np.ascontiguousarray(pcm.samples, dtype=np.int16)
    if pcm.channels > 1 and samples.ndim > 1:
        samples = np.ascontiguousarray(samples.T.reshape(-1), dtype=np.int16)
    return samples.tobytes(), pcm.sample_rate, pcm.channels


def av_video_to_i420(frame: av.VideoFrame) -> tuple[bytes, int, int, float]:
    yuv = frame.reformat(format="yuv420p")
    packed = yuv.to_ndarray()
    duration_ms = 33.0
    if frame.duration is not None and frame.time_base is not None:
        duration_ms = float(frame.duration * frame.time_base) * 1000.0
        if duration_ms <= 0:
            duration_ms = 33.0
    return packed.tobytes(), yuv.width, yuv.height, duration_ms


def i420_to_av_frame(data: bytes, width: int, height: int) -> av.VideoFrame:
    expected = width * height * 3 // 2
    if len(data) < expected:
        data = data + bytes(expected - len(data))
    array = np.frombuffer(data[:expected], dtype=np.uint8).reshape(
        (height * 3 // 2, width)
    )
    return av.VideoFrame.from_ndarray(array, format="yuv420p")


class RemoteMediaTrack(MediaStreamTrack):
    """Inbound Rust RemoteTrack exposed as a duck-typed MediaStreamTrack."""

    def __init__(self, remote_track: Any, user: Any = None) -> None:
        super().__init__()
        kind = remote_track.track_type
        if kind in ("screenshare", "screen_share"):
            kind = "video"
        elif kind in ("screenshare_audio", "screen_share_audio"):
            kind = "audio"
        self.kind = kind
        prefix = remote_track.track_lookup_prefix or remote_track.session_id
        self._id = f"{prefix}:{kind}:0"
        self._remote = remote_track
        self.user = user
        self._relay = FrameRelay(self.kind, self._id)
        self._primary = self._relay.subscribe()
        self._ended = False

    def subscribe(self) -> QueueTrack:
        return self._relay.subscribe()

    async def recv(self):
        if self.readyState != "live":
            raise MediaStreamError("Track is ended")
        return await self._primary.recv()

    async def next_decoded(self) -> Optional[Any]:
        if self._ended or self.readyState != "live":
            return None
        if self.kind == "audio":
            frame = await self._remote.next_pcm()
            if frame is None:
                self._ended = True
                self.stop()
                self._relay.close()
                return None
            av_frame = pcm_bytes_to_av_frame(
                bytes(frame.samples), frame.sample_rate, frame.channels
            )
            await self._relay.push(av_frame)
            return frame
        frame = await self._remote.next_video_frame()
        if frame is None:
            self._ended = True
            self.stop()
            self._relay.close()
            return None
        av_frame = i420_to_av_frame(bytes(frame.data), frame.width, frame.height)
        await self._relay.push(av_frame)
        return frame
