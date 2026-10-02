import asyncio
import contextlib
import logging
import uuid
from typing import AsyncIterator
from unittest.mock import AsyncMock, MagicMock, patch

import numpy as np
import pytest
from dotenv import load_dotenv

from getstream import AsyncStream, _rust
from getstream.models import CallRequest, FullUserResponse, UserRequest
from getstream.video import rtc
from getstream.video.rtc import AudioStreamTrack, CallingState, PcmData
from getstream.video.rtc.connection_manager import ConnectionManager
from getstream.video.rtc.pb.stream.video.sfu.models import models_pb2
from getstream.video.rtc.tracks import SubscriptionConfig, TrackSubscriptionConfig
from tests.rtc.video_source import FrameSource

load_dotenv()

SAMPLE_RATE = 48000
VIDEO_WIDTH = 320
VIDEO_HEIGHT = 240
VIDEO_FPS = 15


@contextlib.contextmanager
def patched_dependencies():
    """Patch heavy ConnectionManager dependencies for unit testing."""
    with (
        patch("getstream.video.rtc.connection_manager.PeerConnectionManager"),
        patch("getstream.video.rtc.connection_manager.NetworkMonitor"),
        patch("getstream.video.rtc.connection_manager.ReconnectionManager"),
        patch("getstream.video.rtc.connection_manager.SubscriptionManager"),
        patch("getstream.video.rtc.connection_manager.ParticipantsState"),
        patch("getstream.video.rtc.connection_manager.Tracer"),
        patch(
            "getstream.video.rtc.connection_manager.asyncio.sleep",
            new_callable=AsyncMock,
        ),
    ):
        yield


@pytest.fixture
def client():
    return AsyncStream(timeout=10.0)


@pytest.fixture
def call_id() -> str:
    return str(uuid.uuid4())


@pytest.fixture
async def connection(
    client: AsyncStream, call_id: str, call_users: list[FullUserResponse]
) -> AsyncIterator[ConnectionManager]:
    call = client.video.call("default", call_id)
    async with await rtc.join(call, call_users[0].id) as connection:
        yield connection


@pytest.fixture
async def peer_call(client: AsyncStream, call_id: str) -> AsyncIterator[_rust.Call]:
    call = _rust.Client(client.api_key, client.api_secret).call("default", call_id)
    yield call
    await call.leave()


@pytest.fixture
def tone() -> np.ndarray:
    t = np.arange(SAMPLE_RATE) / SAMPLE_RATE
    return (np.sin(2 * np.pi * 440 * t) * 10000).astype(np.int16)


@pytest.fixture
async def peer_video(
    client: AsyncStream,
    call_id: str,
    call_users: list[FullUserResponse],
    peer_call: _rust.Call,
) -> AsyncIterator[None]:
    """The second user publishes VP9 video before the test joins."""
    call = client.video.call("default", call_id)
    await call.get_or_create(data=CallRequest(created_by_id=call_users[0].id))
    await peer_call.join(call_users[1].id, create=False)
    video = _rust.LocalVideoTrack.vp9()
    await peer_call.publish_video(video)
    frame = np.full(VIDEO_WIDTH * VIDEO_HEIGHT * 3 // 2, 128, dtype=np.uint8)

    async def write_forever() -> None:
        while True:
            await video.write_i420(frame, VIDEO_WIDTH, VIDEO_HEIGHT, 1 / VIDEO_FPS)
            await asyncio.sleep(1 / VIDEO_FPS)

    task = asyncio.create_task(write_forever())
    yield
    task.cancel()


class TestConnectionManager:
    @pytest.mark.asyncio
    @pytest.mark.integration
    async def test_leave_twice_does_not_hang(self, client: AsyncStream):
        """Integration test: join a real call and leave twice without hanging."""
        call_id = str(uuid.uuid4())
        call = client.video.call("default", call_id)

        async with await rtc.join(call, "test-user") as connection:
            assert connection.connection_state == CallingState.JOINED

            await asyncio.sleep(2)

            await asyncio.wait_for(connection.leave(), timeout=10.0)
            assert connection.connection_state == CallingState.LEFT

            # Second leave must not hang
            await asyncio.wait_for(connection.leave(), timeout=10.0)
            assert connection.connection_state == CallingState.LEFT

    @pytest.mark.asyncio
    @pytest.mark.integration
    async def test_token_only_client_can_join_call(self, client: AsyncStream):
        """A token-only AsyncStream can join a call created by a secret-holding client."""
        call_id = str(uuid.uuid4())
        user_id = f"test-user-{uuid.uuid4()}"
        call_cid = f"default:{call_id}"

        await client.upsert_users(UserRequest(id=user_id))

        server_call = client.video.call("default", call_id)
        await server_call.get_or_create(data=CallRequest(created_by_id="test-admin"))

        user_token = client.create_call_token(user_id, call_cids=[call_cid])

        async with AsyncStream(
            api_key=client.api_key,
            token=user_token,
            base_url=client.base_url,
            timeout=10.0,
        ) as token_client:
            assert token_client.has_api_secret is False

            token_call = token_client.video.call("default", call_id)

            async with await rtc.join(token_call, user_id) as connection:
                assert connection.connection_state == CallingState.JOINED
                await asyncio.sleep(2)
                await asyncio.wait_for(connection.leave(), timeout=10.0)
                assert connection.connection_state == CallingState.LEFT

    def test_rejects_negative_max_join_retries(self):
        """max_join_retries must be >= 0."""
        with (
            patched_dependencies(),
            pytest.raises(ValueError, match="max_join_retries must be >= 0"),
        ):
            ConnectionManager(call=MagicMock(), user_id="user1", max_join_retries=-1)


@pytest.mark.integration
class TestConnectionManagerEvents:
    async def test_participant_joined(
        self,
        connection: ConnectionManager,
        peer_call: _rust.Call,
        call_users: list[FullUserResponse],
    ):
        events: asyncio.Queue[_rust.ParticipantJoined] = asyncio.Queue()
        connection.on("participant_joined", events.put_nowait)

        await peer_call.join(call_users[1].id)

        event = await asyncio.wait_for(events.get(), timeout=10)
        assert event.participant.user_id == call_users[1].id

    async def test_track_added(
        self,
        connection: ConnectionManager,
        peer_call: _rust.Call,
        call_users: list[FullUserResponse],
        tone: np.ndarray,
    ):
        tracks: asyncio.Queue[_rust.RemoteTrack] = asyncio.Queue()
        connection.on("track_added", tracks.put_nowait)
        await peer_call.join(call_users[1].id)
        audio = _rust.LocalAudioTrack()
        await peer_call.publish_audio(audio)

        await audio.write_pcm(tone, SAMPLE_RATE, 1)

        track = await asyncio.wait_for(tracks.get(), timeout=10)
        assert track.participant.user_id == call_users[1].id
        assert track.track_type == _rust.TrackType.AUDIO

    async def test_audio(
        self,
        connection: ConnectionManager,
        peer_call: _rust.Call,
        call_users: list[FullUserResponse],
        tone: np.ndarray,
    ):
        frames: asyncio.Queue[PcmData] = asyncio.Queue()
        connection.on("audio", frames.put_nowait)
        await peer_call.join(call_users[1].id)
        audio = _rust.LocalAudioTrack()
        await peer_call.publish_audio(audio)

        await audio.write_pcm(tone, SAMPLE_RATE, 1)

        while True:
            pcm = await asyncio.wait_for(frames.get(), timeout=10)
            if np.abs(pcm.samples).max() > 1000:
                break
        following = await asyncio.wait_for(frames.get(), timeout=10)
        assert pcm.participant.user_id == call_users[1].id
        assert pcm.sample_rate == SAMPLE_RATE
        assert pcm.time_base == 1 / SAMPLE_RATE
        assert (following.pts - pcm.pts) % 2**32 == len(pcm.samples)

    async def test_participants_state(
        self,
        connection: ConnectionManager,
        peer_call: _rust.Call,
        call_users: list[FullUserResponse],
    ):
        lists: asyncio.Queue[list[_rust.RemoteParticipant]] = asyncio.Queue()
        # The subscription keeps the weakly referenced handler alive.
        subscription = connection.participants_state.map(lists.put_nowait)

        user_ids = {p.user_id for p in await lists.get()}
        assert call_users[0].id in user_ids

        await peer_call.join(call_users[1].id)
        while call_users[1].id not in user_ids:
            user_ids = {p.user_id for p in await asyncio.wait_for(lists.get(), 10)}
        await peer_call.leave()
        while call_users[1].id in user_ids:
            user_ids = {p.user_id for p in await asyncio.wait_for(lists.get(), 10)}
        subscription.unsubscribe()

    async def test_failing_handler_does_not_stop_the_events(
        self,
        connection: ConnectionManager,
        peer_call: _rust.Call,
        call_users: list[FullUserResponse],
    ):
        left: asyncio.Queue[_rust.ParticipantLeft] = asyncio.Queue()

        def fail(event: _rust.ParticipantJoined) -> None:
            raise RuntimeError("handler failed")

        connection.on("participant_joined", fail)
        connection.on("participant_left", left.put_nowait)

        await peer_call.join(call_users[1].id)
        await peer_call.leave()

        event = await asyncio.wait_for(left.get(), timeout=10)
        assert event.participant.user_id == call_users[1].id

    async def test_failing_state_handler_does_not_stop_wait(
        self, client: AsyncStream, call_id: str, call_users: list[FullUserResponse]
    ):
        def fail(change: dict[str, CallingState]) -> None:
            raise RuntimeError("handler failed")

        call = client.video.call("default", call_id)
        connection = await rtc.join(call, call_users[0].id)
        connection.on("connection.state_changed", fail)

        async with connection:
            await call.end()
            await asyncio.wait_for(connection.wait(), timeout=10)

    async def test_cancelled_connect_leaves_the_call(
        self, client: AsyncStream, call_id: str, call_users: list[FullUserResponse]
    ):
        config = SubscriptionConfig(
            default=TrackSubscriptionConfig(track_types=[models_pb2.TRACK_TYPE_AUDIO])
        )
        call = client.video.call("default", call_id)
        connection = await rtc.join(call, call_users[0].id, subscription_config=config)
        connect = asyncio.create_task(connection.connect())

        def cancel_after_join(participants: list[_rust.RemoteParticipant]) -> None:
            # Called while connect() fills the list, after the SDK join.
            if participants:
                connect.cancel()

        subscription = connection.participants_state.map(cancel_after_join)
        with pytest.raises(asyncio.CancelledError):
            await connect
        subscription.unsubscribe()

        assert connection.connection_state == CallingState.LEFT

    async def test_unknown_track_type_in_subscription_config_is_ignored(
        self, client: AsyncStream, call_id: str, call_users: list[FullUserResponse]
    ):
        config = SubscriptionConfig(
            default=TrackSubscriptionConfig(
                track_types=[
                    models_pb2.TRACK_TYPE_UNSPECIFIED,
                    models_pb2.TRACK_TYPE_AUDIO,
                ]
            )
        )
        call = client.video.call("default", call_id)

        async with await rtc.join(
            call, call_users[0].id, subscription_config=config
        ) as connection:
            assert connection.connection_state == CallingState.JOINED

    async def test_wait_returns_when_call_ends(
        self, client: AsyncStream, connection: ConnectionManager, call_id: str
    ):
        await client.video.call("default", call_id).end()

        await asyncio.wait_for(connection.wait(), timeout=10)

    async def test_connection_state_changed(
        self, client: AsyncStream, call_id: str, call_users: list[FullUserResponse]
    ):
        changes: list[dict[str, CallingState]] = []
        call = client.video.call("default", call_id)
        connection = await rtc.join(call, call_users[0].id)
        connection.on("connection.state_changed", changes.append)

        async with connection:
            pass

        assert changes == [
            {"old": CallingState.IDLE, "new": CallingState.JOINING},
            {"old": CallingState.JOINING, "new": CallingState.JOINED},
            {"old": CallingState.JOINED, "new": CallingState.LEFT},
        ]

    async def test_call_ended_is_emitted_once_when_call_ends(
        self, client: AsyncStream, connection: ConnectionManager, call_id: str
    ):
        ended: list[_rust.CallEnded] = []
        connection.on("call_ended", ended.append)

        await client.video.call("default", call_id).end()
        await asyncio.wait_for(connection.wait(), timeout=10)
        await connection.leave()

        assert len(ended) == 1
        assert isinstance(ended[0], _rust.CallEnded)


@pytest.mark.integration
class TestConnectionManagerLogging:
    async def test_sdk_logs_reach_python_logging(
        self,
        client: AsyncStream,
        call_id: str,
        call_users: list[FullUserResponse],
        caplog: pytest.LogCaptureFixture,
    ):
        # Stops the forwarding that the autouse fixture set up.
        _rust.configure_logging(None, logging.NOTSET)
        caplog.set_level(logging.DEBUG, logger="getstream")

        call = client.video.call("default", call_id)
        async with await rtc.join(call, call_users[0].id):
            pass
        # Returns after the queued records are delivered.
        _rust.configure_logging(None, logging.NOTSET)

        assert any(
            record.name.startswith("getstream.rtc.") for record in caplog.records
        )


@pytest.fixture
async def agent_audio(
    connection: ConnectionManager,
    peer_call: _rust.Call,
    call_users: list[FullUserResponse],
) -> AsyncIterator[tuple[AudioStreamTrack, _rust.TrackStream]]:
    """The agent publishes an AudioStreamTrack; the peer receives audio."""
    tracks = peer_call.tracks()
    await peer_call.join(call_users[1].id)
    await peer_call.update_subscriptions(
        _rust.SubscriptionConfig(
            default=_rust.TrackSubscriptionConfig(track_types=[_rust.TrackType.AUDIO])
        )
    )
    audio = AudioStreamTrack()
    await connection.add_tracks(audio=audio)
    yield audio, tracks


async def next_loud_frame(track: _rust.RemoteTrack) -> _rust.PcmFrame:
    while True:
        frame = await track.next_pcm()
        if np.abs(frame.samples).max() > 1000:
            return frame


async def next_silent_frame(track: _rust.RemoteTrack) -> _rust.PcmFrame:
    while True:
        frame = await track.next_pcm()
        if np.abs(frame.samples).max() < 100:
            return frame


@pytest.mark.integration
class TestConnectionManagerPublishing:
    async def test_add_tracks_publishes_audio(
        self,
        agent_audio: tuple[AudioStreamTrack, _rust.TrackStream],
        call_users: list[FullUserResponse],
        tone: np.ndarray,
    ):
        audio, tracks = agent_audio
        pcm = PcmData(samples=tone, sample_rate=SAMPLE_RATE, format="s16", channels=1)

        for _ in range(5):
            await audio.write(pcm)

        track = await asyncio.wait_for(anext(tracks), timeout=15)
        assert track.participant.user_id == call_users[0].id
        await asyncio.wait_for(next_loud_frame(track), timeout=10)

    async def test_flush_drops_the_queued_audio(
        self,
        agent_audio: tuple[AudioStreamTrack, _rust.TrackStream],
        tone: np.ndarray,
    ):
        audio, tracks = agent_audio
        pcm = PcmData(samples=tone, sample_rate=SAMPLE_RATE, format="s16", channels=1)
        for _ in range(20):
            await audio.write(pcm)
        track = await asyncio.wait_for(anext(tracks), timeout=15)
        await asyncio.wait_for(next_loud_frame(track), timeout=10)

        await audio.flush()

        # Without the flush, the tone would play for about 20 s.
        await asyncio.wait_for(next_silent_frame(track), timeout=5)


@pytest.mark.integration
class TestConnectionManagerVideoPublishing:
    async def test_video_keeps_the_first_size(
        self,
        connection: ConnectionManager,
        peer_call: _rust.Call,
        call_users: list[FullUserResponse],
    ):
        tracks = peer_call.tracks()
        await peer_call.join(call_users[1].id)
        await peer_call.update_subscriptions(
            _rust.SubscriptionConfig(
                default=_rust.TrackSubscriptionConfig(
                    track_types=[_rust.TrackType.VIDEO]
                )
            )
        )
        # 4 s at the first size, then a size that the SDK encoder rejects
        # unless the forwarder scales it.
        source = FrameSource([(320, 240)] * 60 + [(640, 480)] * 300)
        await connection.add_tracks(video=source)

        track = await asyncio.wait_for(anext(tracks), timeout=15)
        assert track.participant.user_id == call_users[0].id
        frames = track.video_frames()
        # 90 received frames end well after the size change.
        for _ in range(90):
            frame = await asyncio.wait_for(anext(frames), timeout=10)
        assert (frame.width, frame.height) == (320, 240)

    async def test_stopped_video_track_is_unpublished(
        self,
        connection: ConnectionManager,
        peer_call: _rust.Call,
        call_users: list[FullUserResponse],
    ):
        events = peer_call.sfu_events()
        await peer_call.join(call_users[1].id)
        source = FrameSource([(320, 240)] * 300)
        await connection.add_tracks(video=source)
        async for event in events:
            if (
                isinstance(event, _rust.TrackPublished)
                and event.user_id == call_users[0].id
            ):
                break

        source.stop()

        async for event in events:
            if (
                isinstance(event, _rust.TrackUnpublished)
                and event.user_id == call_users[0].id
            ):
                break
        assert event.track_type == _rust.TrackType.VIDEO


@pytest.mark.integration
class TestConnectionManagerSubscriptions:
    async def test_default_rule_subscribes_to_video(
        self,
        client: AsyncStream,
        call_id: str,
        call_users: list[FullUserResponse],
        peer_video: None,
    ):
        config = SubscriptionConfig(
            default=TrackSubscriptionConfig(track_types=[models_pb2.TRACK_TYPE_VIDEO])
        )
        tracks: asyncio.Queue[_rust.RemoteTrack] = asyncio.Queue()
        call = client.video.call("default", call_id)
        connection = await rtc.join(
            call, call_users[0].id, create=False, subscription_config=config
        )
        connection.on("track_added", tracks.put_nowait)

        async with connection:
            track = await asyncio.wait_for(tracks.get(), timeout=15)

        assert track.track_type == _rust.TrackType.VIDEO
        assert track.participant.user_id == call_users[1].id

    async def test_role_rule_subscribes_to_video(
        self,
        client: AsyncStream,
        call_id: str,
        call_users: list[FullUserResponse],
        peer_video: None,
    ):
        config = SubscriptionConfig(
            role_filters={
                "user": TrackSubscriptionConfig(
                    track_types=[models_pb2.TRACK_TYPE_VIDEO]
                )
            }
        )
        tracks: asyncio.Queue[_rust.RemoteTrack] = asyncio.Queue()
        call = client.video.call("default", call_id)
        connection = await rtc.join(
            call, call_users[0].id, create=False, subscription_config=config
        )
        connection.on("track_added", tracks.put_nowait)

        async with connection:
            track = await asyncio.wait_for(tracks.get(), timeout=15)

        assert track.track_type == _rust.TrackType.VIDEO
