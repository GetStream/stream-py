import asyncio
import fractions

import aiortc
import av
import getstream_rtc
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


STRIPE_WIDTH = 64


class TimedFrameSource(aiortc.MediaStreamTrack):
    """An aiortc video track that gives 320x240 frames with the given `pts`
    values on the 90 kHz clock, each at its time, and then ends. Frame `i` shows
    `i` in binary as 5 vertical stripes, white for 1 and black for 0, lowest
    bit on the left."""

    kind = "video"

    def __init__(self, pts_values: list[int]) -> None:
        super().__init__()
        self._pts_values = list(pts_values)
        self._number = 0
        self._previous_pts = 0

    async def recv(self) -> av.VideoFrame:
        if self.readyState != "live" or self._number == len(self._pts_values):
            raise aiortc.mediastreams.MediaStreamError
        pts = self._pts_values[self._number]
        await asyncio.sleep((pts - self._previous_pts) / VIDEO_CLOCK_RATE)
        self._previous_pts = pts
        pixels = np.zeros((240, 320, 3), dtype=np.uint8)
        for bit in range(5):
            if self._number >> bit & 1:
                pixels[:, bit * STRIPE_WIDTH : (bit + 1) * STRIPE_WIDTH] = 255
        self._number += 1
        frame = av.VideoFrame.from_ndarray(pixels, format="rgb24")
        frame.pts = pts
        frame.time_base = fractions.Fraction(1, VIDEO_CLOCK_RATE)
        return frame


def frame_number(frame: getstream_rtc.VideoFrame) -> int:
    """The number that `TimedFrameSource` shows in a received frame."""
    middle_row = frame.data[frame.width * (frame.height // 2) :][: frame.width]
    return sum(
        1 << bit
        for bit in range(5)
        if middle_row[bit * STRIPE_WIDTH + STRIPE_WIDTH // 2] > 128
    )
