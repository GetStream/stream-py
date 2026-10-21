from typing import cast

import aiortc
import av
import getstream_rtc
import numpy as np
from numpy.typing import NDArray

# The duration of a frame whose source gives no timing, in seconds.
_DEFAULT_FRAME_DURATION = 1 / 30


class VideoForwarder:
    """Copies the frames of an aiortc video track to an SDK `LocalVideoTrack`.

    The source paces the frames. The SDK encoder needs one even size for the
    whole track, so each frame is scaled to the size of the first frame, with an
    odd width or height raised to the next even value.
    """

    def __init__(
        self, source: aiortc.MediaStreamTrack, target: getstream_rtc.LocalVideoTrack
    ) -> None:
        self.source = source
        self.target = target

    async def run(self) -> None:
        """Copy frames until the source ends or the SDK stops the target."""
        size: tuple[int, int] | None = None
        previous_time: float | None = None
        pts: float | None = None
        while True:
            try:
                # aiortc types recv() as a frame or a packet; a video track
                # gives video frames.
                frame = cast(av.VideoFrame, await self.source.recv())
            except aiortc.mediastreams.MediaStreamError:
                return
            if size is None:
                size = (_even(frame.width), _even(frame.height))
            # `time` is pts * time_base, or None when the frame has no pts. The
            # SDK drops a frame whose pts is not after the previous one, so a
            # frame without a later time than the previous frame comes one
            # default frame length after it.
            time = frame.time
            gap = (
                time - previous_time
                if time is not None
                and previous_time is not None
                and time > previous_time
                else _DEFAULT_FRAME_DURATION
            )
            pts = 0.0 if pts is None else pts + gap
            previous_time = time
            width, height = size
            frame = frame.reformat(width=width, height=height, format="yuv420p")
            # A yuv420p frame gives uint8 planes.
            pixels = cast(NDArray[np.uint8], frame.to_ndarray())
            try:
                await self.target.write_i420_at(pixels.reshape(-1), width, height, pts)
            except getstream_rtc.IllegalStateError:
                # The only cause is a stopped track: it was unpublished, or the
                # call was left or ended.
                return


def _even(value: int) -> int:
    return value + value % 2
