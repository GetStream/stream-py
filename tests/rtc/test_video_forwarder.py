import asyncio

from getstream import _rust
from getstream.video.rtc.video_forwarder import VideoForwarder
from tests.rtc.video_source import FrameSource


class TestVideoForwarder:
    async def test_run_returns_when_the_source_ends(self):
        source = FrameSource([(320, 240)])

        await asyncio.wait_for(
            VideoForwarder(source, _rust.LocalVideoTrack.vp9()).run(), timeout=5
        )

    async def test_odd_and_changed_sizes_are_written(self):
        # The SDK encoder rejects odd sizes; the forwarder scales them.
        source = FrameSource([(321, 241), (640, 480), (320, 240)])

        await asyncio.wait_for(
            VideoForwarder(source, _rust.LocalVideoTrack.vp9()).run(), timeout=5
        )
