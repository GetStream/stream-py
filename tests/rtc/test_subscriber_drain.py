"""Tests for SubscriberPeerConnection video drain behavior."""

from unittest.mock import AsyncMock, Mock

import pytest
from aiortc.contrib.media import MediaRelay

from getstream.video.rtc.pc import SubscriberPeerConnection


@pytest.fixture
def subscriber_pc():
    """Create a SubscriberPeerConnection bypassing heavy parent inits."""
    pc = SubscriberPeerConnection.__new__(SubscriberPeerConnection)
    pc.connection = Mock()
    pc._drain_video_frames = True
    pc.track_map = {}
    pc.video_frame_trackers = {}
    pc._video_blackholes = {}
    pc._video_drain_tasks = {}
    pc._listeners = {}
    return pc


class TestAddTrackSubscriberStopsDrain:
    def test_blackhole_stopped_when_subscriber_added(self, subscriber_pc):
        track_id = "user123:video:0"
        relay = MediaRelay()
        original_track = Mock()
        subscriber_pc.track_map[track_id] = (relay, original_track)

        blackhole = Mock()
        blackhole.stop = AsyncMock()
        subscriber_pc._video_blackholes[track_id] = blackhole
        subscriber_pc._video_drain_tasks[track_id] = Mock()

        subscriber_pc.add_track_subscriber(track_id)

        blackhole.stop.assert_called_once()
        assert track_id not in subscriber_pc._video_blackholes
        assert track_id not in subscriber_pc._video_drain_tasks

    def test_no_error_when_no_drain_exists(self, subscriber_pc):
        track_id = "user123:video:0"
        relay = MediaRelay()
        original_track = Mock()
        subscriber_pc.track_map[track_id] = (relay, original_track)

        result = subscriber_pc.add_track_subscriber(track_id)
        assert result is not None
