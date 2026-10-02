import aiortc

from getstream import _rust

# The duration of a frame whose source gives no timing, in seconds.
_DEFAULT_FRAME_DURATION = 1 / 30


class VideoForwarder:
    """Copies the frames of an aiortc video track to an SDK `LocalVideoTrack`.

    The source paces the frames. The SDK encoder needs one even size for the
    whole track, so each frame is scaled to the size of the first frame, with an
    odd width or height raised to the next even value.
    """

    def __init__(
        self, source: aiortc.MediaStreamTrack, target: _rust.LocalVideoTrack
    ) -> None:
        self.source = source
        self.target = target

    async def run(self) -> None:
        """Copy frames until the source ends."""
        size: tuple[int, int] | None = None
        previous_time: float | None = None
        while True:
            try:
                frame = await self.source.recv()
            except aiortc.mediastreams.MediaStreamError:
                return
            if size is None:
                size = (_even(frame.width), _even(frame.height))
            # `time` is pts * time_base, or None when the frame has no pts.
            time = frame.time
            duration = (
                time - previous_time
                if time is not None
                and previous_time is not None
                and time > previous_time
                else _DEFAULT_FRAME_DURATION
            )
            previous_time = time
            width, height = size
            frame = frame.reformat(width=width, height=height, format="yuv420p")
            await self.target.write_i420(
                frame.to_ndarray().reshape(-1), width, height, duration
            )


def _even(value: int) -> int:
    return value + value % 2
