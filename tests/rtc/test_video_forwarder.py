import asyncio

import getstream_rtc
import pytest

from getstream.video.rtc.video_forwarder import VideoForwarder
from tests.rtc.video_source import FrameSource


class TestVideoForwarder:
    async def test_run_returns_when_the_source_ends(self):
        source = FrameSource([(320, 240)])

        await asyncio.wait_for(
            VideoForwarder(source, getstream_rtc.LocalVideoTrack.vp9()).run(), timeout=5
        )

    async def test_odd_and_changed_sizes_are_written(self):
        # The SDK encoder rejects odd sizes; the forwarder scales them.
        source = FrameSource([(321, 241), (640, 480), (320, 240)])

        await asyncio.wait_for(
            VideoForwarder(source, getstream_rtc.LocalVideoTrack.vp9()).run(), timeout=5
        )


@pytest.mark.integration
class TestVideoForwarderOnACall:
    async def test_run_returns_when_the_call_is_left(
        self, joined_call: getstream_rtc.Call
    ):
        target = getstream_rtc.LocalVideoTrack.vp9()
        await joined_call.publish_video(target)
        # 10 s of video, so only the stopped track can end the run in time.
        source = FrameSource([(320, 240)] * 150)
        run = asyncio.create_task(VideoForwarder(source, target).run())
        await asyncio.sleep(0.5)

        # Leaving stops the published track.
        await joined_call.leave()

        await asyncio.wait_for(run, timeout=5)
