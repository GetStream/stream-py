"""Tests for video frame tracking and stats injection."""

import asyncio
import pytest
import av
from unittest.mock import Mock
from aiortc import RTCPeerConnection, RTCConfiguration, RTCIceServer
from aiortc.mediastreams import MediaStreamError


def create_video_frame(width: int = 320, height: int = 240) -> av.VideoFrame:
    """Create a real av.VideoFrame for testing."""
    return av.VideoFrame(width, height, "rgb24")


class MockVideoTrack:
    """Mock video track for testing frame trackers."""

    kind = "video"

    def __init__(self, frames: list, delay_ms: float = 0):
        self.frames = frames
        self.frame_index = 0
        self.delay_ms = delay_ms
        self.id = "mock-track"
        self._ended = False

    @property
    def readyState(self):
        return "ended" if self._ended else "live"

    async def recv(self):
        if self.frame_index >= len(self.frames):
            self._ended = True
            raise MediaStreamError("Track ended")
        if self.delay_ms > 0:
            await asyncio.sleep(self.delay_ms / 1000)
        frame = self.frames[self.frame_index]
        self.frame_index += 1
        return frame

    def stop(self):
        self._ended = True


class TestVideoFrameTracker:
    """Tests for VideoFrameTracker (subscriber video track wrapper)."""

    @pytest.mark.asyncio
    async def test_tracks_frames_and_dimensions(self):
        """Should count frames, capture dimensions, and accumulate decode time."""
        from getstream.video.rtc.track_util import VideoFrameTracker

        frames = [
            create_video_frame(320, 240),
            create_video_frame(320, 240),
            create_video_frame(160, 120),  # Resolution change
        ]
        tracker = VideoFrameTracker(MockVideoTrack(frames, delay_ms=5))

        for _ in range(3):
            await tracker.recv()

        stats = tracker.get_frame_stats()
        assert stats["framesDecoded"] == 3
        assert stats["frameWidth"] == 160  # Last frame
        assert stats["frameHeight"] == 120
        assert stats["totalDecodeTime"] > 0.01  # At least 15ms accumulated

    @pytest.mark.asyncio
    async def test_handles_track_end(self):
        """Should raise MediaStreamError when track ends."""
        from getstream.video.rtc.track_util import VideoFrameTracker

        tracker = VideoFrameTracker(MockVideoTrack([create_video_frame()]))
        await tracker.recv()

        with pytest.raises(MediaStreamError):
            await tracker.recv()

        # Stats still valid after track ends
        assert tracker.get_frame_stats()["framesDecoded"] == 1


class TestBufferedMediaTrackFrameTracking:
    """Tests for BufferedMediaTrack frame tracking (publisher video)."""

    @pytest.mark.asyncio
    async def test_tracks_frames_through_recv(self):
        """Should track video frames passing through recv()."""
        from getstream.video.rtc.track_util import BufferedMediaTrack

        frames = [create_video_frame(320, 240), create_video_frame(160, 120)]
        buffered = BufferedMediaTrack(MockVideoTrack(frames))

        await buffered.recv()
        await buffered.recv()

        stats = buffered.get_frame_stats()
        assert stats["framesSent"] == 2
        assert stats["frameWidth"] == 160
        assert stats["frameHeight"] == 120


class TestStatsTracerFrameInjection:
    """Tests for StatsTracer frame stats injection."""

    @pytest.mark.asyncio
    async def test_injects_publisher_frame_stats(self):
        """Frame stats from tracker should be injected into outbound-rtp."""
        from getstream.video.rtc.stats_tracer import StatsTracer

        pc = RTCPeerConnection(
            RTCConfiguration(
                iceServers=[RTCIceServer(urls=["stun:stun.l.google.com:19302"])]
            )
        )

        try:
            pc.addTransceiver("video", direction="sendonly")
            await pc.setLocalDescription(await pc.createOffer())
            await asyncio.sleep(0.2)

            tracer = StatsTracer(pc, "publisher")
            tracer.set_frame_tracker(
                Mock(
                    get_frame_stats=lambda: {
                        "framesSent": 100,
                        "frameWidth": 320,
                        "frameHeight": 240,
                        "totalEncodeTime": 0.5,
                    }
                )
            )

            # First get() populates stats with frame data
            result = await tracer.get()

            # Find video outbound-rtp in delta (first call has all fields)
            video_stats = [
                v
                for v in result.delta.values()
                if isinstance(v, dict) and v.get("kind") == "video"
            ]
            assert len(video_stats) > 0
            video_rtp = video_stats[0]
            assert video_rtp["framesSent"] == 100
            assert video_rtp["frameWidth"] == 320
            assert video_rtp["frameHeight"] == 240

        finally:
            await pc.close()

    @pytest.mark.asyncio
    async def test_works_without_frame_tracker(self):
        """Stats collection should work without frame tracker set."""
        from getstream.video.rtc.stats_tracer import StatsTracer

        pc = RTCPeerConnection()

        try:
            pc.addTransceiver("video", direction="sendonly")
            await pc.setLocalDescription(await pc.createOffer())

            tracer = StatsTracer(pc, "publisher")
            # No frame tracker set

            result = await tracer.get()
            assert result.delta is not None
            assert "timestamp" in result.delta

        finally:
            await pc.close()
