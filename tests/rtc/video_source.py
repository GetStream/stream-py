import asyncio
import fractions

import aiortc
import av
import numpy as np

VIDEO_CLOCK_RATE = 90000


class FrameSource(aiortc.MediaStreamTrack):
    """An aiortc video track that gives grey frames of the given sizes, one
    per `1 / fps` seconds, and then ends."""

    kind = "video"

    def __init__(self, sizes: list[tuple[int, int]], fps: int = 15) -> None:
        super().__init__()
        self._sizes = list(sizes)
        self._fps = fps
        self._pts = 0

    async def recv(self) -> av.VideoFrame:
        if self.readyState != "live" or not self._sizes:
            raise aiortc.mediastreams.MediaStreamError
        await asyncio.sleep(1 / self._fps)
        width, height = self._sizes.pop(0)
        frame = av.VideoFrame.from_ndarray(
            np.full((height, width, 3), 128, dtype=np.uint8), format="rgb24"
        )
        frame.pts = self._pts
        frame.time_base = fractions.Fraction(1, VIDEO_CLOCK_RATE)
        self._pts += VIDEO_CLOCK_RATE // self._fps
        return frame
