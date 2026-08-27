import asyncio
from types import SimpleNamespace

import pytest

from getstream.video.rtc.media import FrameRelay, MediaStreamTrack, RemoteMediaTrack
from getstream.video.rtc.peer_connection import PeerConnectionManager
from getstream.video.rtc.recording import RecordingManager, RecordingType


class FakeRemote:
    def __init__(self, track_type: str = "video") -> None:
        self.track_type = track_type
        self.track_lookup_prefix = "prefix"
        self.session_id = "session"
        self.drain_calls = 0
        self.video_frame_calls = 0
        self.pcm_calls = 0
        self.alive = True
        self._pcm = SimpleNamespace(samples=b"\x00\x00", sample_rate=48000, channels=1)
        self._video = SimpleNamespace(data=bytes(6), width=2, height=2)

    async def drain_rtp(self) -> bool:
        self.drain_calls += 1
        await asyncio.sleep(0)
        return self.alive

    async def next_video_frame(self):
        self.video_frame_calls += 1
        await asyncio.sleep(0)
        if not self.alive:
            return None
        return self._video

    async def next_pcm(self):
        self.pcm_calls += 1
        await asyncio.sleep(0)
        if not self.alive:
            return None
        return self._pcm


class CountingTrack(MediaStreamTrack):
    kind = "video"

    def __init__(self) -> None:
        super().__init__()
        self.subscribe_calls = 0

    def subscribe(self, maxsize: int = 32):
        self.subscribe_calls += 1
        return super().subscribe(maxsize=maxsize)


class FakeUser:
    user_id = "alice"


class FakeConnectionManager:
    def __init__(self) -> None:
        self.events = []

    def emit(self, name, payload=None):
        self.events.append((name, payload))


@pytest.mark.asyncio
async def test_idle_remote_video_track_holds_no_decoded_queues():
    wrapper = RemoteMediaTrack(FakeRemote("video"))
    assert wrapper.wants_decoded_frames() is False
    assert wrapper._relay.has_subscribers() is False
    assert wrapper._relay._queues == []


@pytest.mark.asyncio
async def test_subscribe_and_recv_enable_decode():
    wrapper = RemoteMediaTrack(FakeRemote("video"))
    subscribed = wrapper.subscribe()
    assert wrapper.wants_decoded_frames() is True
    assert subscribed.kind == "video"

    recv_wrapper = RemoteMediaTrack(FakeRemote("video"))
    recv_task = asyncio.create_task(recv_wrapper.recv())
    await asyncio.sleep(0)
    assert recv_wrapper.wants_decoded_frames() is True
    recv_task.cancel()
    with pytest.raises(asyncio.CancelledError):
        await recv_task


@pytest.mark.asyncio
async def test_pump_drains_unwatched_video_without_decoding():
    remote = FakeRemote("video")
    wrapper = RemoteMediaTrack(remote)
    manager = PeerConnectionManager(FakeConnectionManager())

    async def stop_after_drains():
        while remote.drain_calls < 3:
            await asyncio.sleep(0)
        remote.alive = False

    await asyncio.wait_for(
        asyncio.gather(manager._pump_remote_track(wrapper, None), stop_after_drains()),
        timeout=1,
    )
    assert remote.drain_calls >= 3
    assert remote.video_frame_calls == 0


@pytest.mark.asyncio
async def test_pump_decodes_video_after_subscribe():
    remote = FakeRemote("video")
    wrapper = RemoteMediaTrack(remote)
    wrapper.subscribe()
    manager = PeerConnectionManager(FakeConnectionManager())

    async def stop_after_decode():
        while remote.video_frame_calls < 2:
            await asyncio.sleep(0)
        remote.alive = False

    await asyncio.wait_for(
        asyncio.gather(manager._pump_remote_track(wrapper, None), stop_after_decode()),
        timeout=1,
    )
    assert remote.video_frame_calls >= 2
    assert remote.drain_calls == 0


@pytest.mark.asyncio
async def test_pump_switches_from_drain_to_decode_on_subscribe():
    remote = FakeRemote("video")
    wrapper = RemoteMediaTrack(remote)
    manager = PeerConnectionManager(FakeConnectionManager())

    async def subscribe_after_drain():
        while remote.drain_calls < 2:
            await asyncio.sleep(0)
        wrapper.subscribe()
        while remote.video_frame_calls < 1:
            await asyncio.sleep(0)
        remote.alive = False

    await asyncio.wait_for(
        asyncio.gather(
            manager._pump_remote_track(wrapper, None), subscribe_after_drain()
        ),
        timeout=1,
    )
    assert remote.drain_calls >= 2
    assert remote.video_frame_calls >= 1


@pytest.mark.asyncio
async def test_idle_recording_does_not_subscribe():
    recording = RecordingManager()
    track = CountingTrack()
    await recording.on_track_received(track, FakeUser())
    assert track.subscribe_calls == 0
    assert track.id in recording._pending_tracks


@pytest.mark.asyncio
async def test_active_track_recording_subscribes_once():
    recording = RecordingManager()
    recording._recording_types.add(RecordingType.TRACK)
    started = []

    async def capture(user_id, track):
        started.append((user_id, track))

    recording._start_user_track_recording = capture
    track = CountingTrack()
    await recording.on_track_received(track, FakeUser())
    assert track.subscribe_calls == 1
    assert started == [("alice", track)]
    assert track.id not in recording._pending_tracks


@pytest.mark.asyncio
async def test_pending_tracks_subscribe_when_recording_starts():
    recording = RecordingManager()
    track = CountingTrack()
    await recording.on_track_received(track, FakeUser())
    assert track.subscribe_calls == 0

    started = []

    async def capture(user_id, consumed):
        started.append(consumed)

    recording._start_user_track_recording = capture
    recording._recording_types.add(RecordingType.TRACK)
    await recording._process_pending_tracks()
    assert track.subscribe_calls == 1
    assert started == [track]


def test_frame_relay_starts_with_zero_queues():
    relay = FrameRelay("video", "track-1")
    assert relay.has_subscribers() is False
    relay.subscribe()
    assert relay.has_subscribers() is True
