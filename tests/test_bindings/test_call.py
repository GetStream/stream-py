import asyncio
import contextlib
import os
import time
import uuid
from typing import AsyncIterator, Iterator

import numpy as np
import pytest

from getstream import Stream, _rust
from getstream.models import CallRequest, FullUserResponse
from getstream.video.rtc.pb.stream.video.sfu.models import models_pb2

SAMPLE_RATE = 48000
FRAME_SAMPLES = SAMPLE_RATE // 50
VIDEO_WIDTH = 320
VIDEO_HEIGHT = 240
VIDEO_FPS = 15
AUDIO = _rust.SubscriptionConfig(
    default=_rust.TrackSubscriptionConfig(track_types=[_rust.TrackType.AUDIO])
)
AUDIO_AND_VIDEO = _rust.SubscriptionConfig(
    default=_rust.TrackSubscriptionConfig(
        track_types=[_rust.TrackType.AUDIO, _rust.TrackType.VIDEO]
    )
)


@pytest.fixture
def call_id() -> str:
    return str(uuid.uuid4())


@pytest.fixture
async def joined_call(
    rust_client: _rust.Client,
    call_id: str,
    call_users: list[FullUserResponse],
) -> AsyncIterator[_rust.Call]:
    call = rust_client.call("default", call_id)
    await call.join(call_users[0].id)
    yield call
    await call.leave()


@pytest.fixture
async def joining_call(
    rust_client: _rust.Client,
    call_id: str,
    call_users: list[FullUserResponse],
) -> AsyncIterator[_rust.Call]:
    call = rust_client.call("default", call_id)
    yield call
    await call.leave()


@pytest.fixture
def tone() -> np.ndarray:
    t = np.arange(FRAME_SAMPLES) / SAMPLE_RATE
    return (np.sin(2 * np.pi * 440 * t) * 10000).astype(np.int16)


@pytest.fixture
async def published_audio(
    joined_call: _rust.Call, tone: np.ndarray
) -> AsyncIterator[_rust.LocalAudioTrack]:
    track = _rust.LocalAudioTrack()
    await joined_call.publish_audio(track)

    async def write_forever() -> None:
        while True:
            await track.write_pcm(tone, SAMPLE_RATE, 1)
            await asyncio.sleep(FRAME_SAMPLES / SAMPLE_RATE)

    task = asyncio.create_task(write_forever())
    yield track
    task.cancel()


@pytest.fixture
async def published_video(
    joined_call: _rust.Call,
) -> AsyncIterator[_rust.LocalVideoTrack]:
    track = _rust.LocalVideoTrack.vp9()
    await joined_call.publish_video(track)
    frame = np.full(VIDEO_WIDTH * VIDEO_HEIGHT * 3 // 2, 128, dtype=np.uint8)

    async def write_forever() -> None:
        while True:
            await track.write_i420(frame, VIDEO_WIDTH, VIDEO_HEIGHT, 1 / VIDEO_FPS)
            await asyncio.sleep(1 / VIDEO_FPS)

    task = asyncio.create_task(write_forever())
    yield track
    task.cancel()


@pytest.fixture
async def remote_video(
    published_video: _rust.LocalVideoTrack,
    joining_call: _rust.Call,
    call_users: list[FullUserResponse],
) -> _rust.RemoteTrack:
    """The track of `published_video` in `joining_call`."""
    tracks = joining_call.tracks()
    await joining_call.join(call_users[1].id)
    await joining_call.update_subscriptions(AUDIO_AND_VIDEO)
    return await anext(
        track async for track in tracks if track.track_type == _rust.TrackType.VIDEO
    )


async def rtp_timestamps(frames: _rust.VideoFrameStream, count: int) -> list[int]:
    return [(await anext(frames)).rtp_timestamp for _ in range(count)]


async def read_to_end(frames: _rust.VideoFrameStream) -> list[_rust.VideoFrame]:
    return [frame async for frame in frames]


@pytest.fixture
def live_call_id(
    client: Stream, call_id: str, call_users: list[FullUserResponse]
) -> Iterator[str]:
    call = client.video.call("livestream", call_id)
    call.get_or_create(data=CallRequest(created_by_id=call_users[0].id))
    call.go_live()
    yield call_id
    call.end()


@pytest.fixture
async def viewer_call(
    rust_client: _rust.Client,
    live_call_id: str,
    call_users: list[FullUserResponse],
) -> AsyncIterator[_rust.Call]:
    call = rust_client.call("livestream", live_call_id)
    await call.join(call_users[1].id, create=False)
    yield call
    await call.leave()


@pytest.mark.integration
class TestCallJoin:
    async def test_join_and_leave(
        self, rust_client: _rust.Client, call_users: list[FullUserResponse]
    ):
        call = rust_client.call("default", str(uuid.uuid4()))

        await call.join(call_users[0].id)
        assert call.calling_state == _rust.CallingState.JOINED
        assert await call.session_id()

        await call.leave()
        assert call.calling_state == _rust.CallingState.LEFT

    async def test_join_with_user_token(
        self,
        client: Stream,
        joined_call: _rust.Call,
        call_id: str,
        call_users: list[FullUserResponse],
    ):
        token = client.create_call_token(
            call_users[1].id, call_cids=[f"default:{call_id}"]
        )
        call = _rust.Client(os.environ["STREAM_API_KEY"], token=token).call(
            "default", call_id
        )

        await call.join(call_users[1].id, create=False)
        assert call.calling_state == _rust.CallingState.JOINED
        await call.leave()

    async def test_join_with_wrong_secret_raises(
        self, call_users: list[FullUserResponse]
    ):
        client = _rust.Client(os.environ["STREAM_API_KEY"], "wrong-secret")
        call = client.call("default", str(uuid.uuid4()))

        with pytest.raises(_rust.CoordinatorError):
            await call.join(call_users[0].id)

    async def test_join_with_unknown_call_type_raises(
        self, rust_client: _rust.Client, call_users: list[FullUserResponse]
    ):
        call = rust_client.call("missingtype", str(uuid.uuid4()))

        with pytest.raises(_rust.ApiError) as exc_info:
            await call.join(call_users[0].id)

        assert exc_info.value.status_code == 404
        assert exc_info.value.code == 16
        assert exc_info.value.message

    async def test_cancelled_join_allows_new_join(
        self, rust_client: _rust.Client, call_users: list[FullUserResponse]
    ):
        call = rust_client.call("default", str(uuid.uuid4()))

        join = call.join(call_users[0].id)
        await asyncio.sleep(0.1)
        join.cancel()
        with pytest.raises(asyncio.CancelledError):
            await join

        await call.join(call_users[0].id)
        assert call.calling_state == _rust.CallingState.JOINED
        await call.leave()

    async def test_leave_during_join(
        self, rust_client: _rust.Client, call_users: list[FullUserResponse]
    ):
        call = rust_client.call("default", str(uuid.uuid4()))

        join = call.join(call_users[0].id)
        await asyncio.sleep(0.1)
        await call.leave()
        # A fast join can finish before the leave stops it.
        with contextlib.suppress(_rust.RtcError):
            await join
        assert call.calling_state == _rust.CallingState.LEFT

        await call.join(call_users[0].id)
        assert call.calling_state == _rust.CallingState.JOINED
        await call.leave()

    async def test_join_during_leave(
        self, rust_client: _rust.Client, call_users: list[FullUserResponse]
    ):
        call = rust_client.call("default", str(uuid.uuid4()))
        await call.join(call_users[0].id)

        leave = call.leave()
        with contextlib.suppress(_rust.IllegalStateError):
            await call.join(call_users[0].id)
        await leave

        # The join failed while the leave ran (LEFT), or it ran after the
        # leave finished (JOINED).
        if call.calling_state == _rust.CallingState.LEFT:
            await call.join(call_users[0].id)
        assert call.calling_state == _rust.CallingState.JOINED
        await call.leave()


class TestCallPublish:
    async def test_publish_before_join_raises(self, call_id: str):
        call = _rust.Client("key", "secret").call("default", call_id)

        with pytest.raises(_rust.IllegalStateError):
            await call.publish_audio(_rust.LocalAudioTrack())

    @pytest.mark.integration
    async def test_publish_without_capability_raises(self, viewer_call: _rust.Call):
        with pytest.raises(_rust.PermissionDeniedError) as exc_info:
            await viewer_call.publish_audio(_rust.LocalAudioTrack())

        assert exc_info.value.capability == "send-audio"

    @pytest.mark.integration
    async def test_stop_publish_audio_unpublishes_track(
        self,
        joined_call: _rust.Call,
        joining_call: _rust.Call,
        call_users: list[FullUserResponse],
        tone: np.ndarray,
    ):
        track = _rust.LocalAudioTrack()
        await joined_call.publish_audio(track)
        await joining_call.join(call_users[1].id)
        events = joining_call.sfu_events()

        await joined_call.stop_publish_audio(track)
        async for event in events:
            if (
                isinstance(event, _rust.TrackUnpublished)
                and event.user_id == call_users[0].id
            ):
                break
        assert event.track_type == _rust.TrackType.AUDIO
        with pytest.raises(_rust.IllegalStateError):
            await track.write_pcm(tone, SAMPLE_RATE, 1)

    @pytest.mark.integration
    async def test_mute_unpublishes_track_with_user_muted(
        self,
        published_audio: _rust.LocalAudioTrack,
        joined_call: _rust.Call,
        joining_call: _rust.Call,
        call_users: list[FullUserResponse],
    ):
        await joining_call.join(call_users[1].id)
        events = joining_call.sfu_events()

        await joined_call.mute_track(_rust.TrackType.AUDIO)
        async for event in events:
            if (
                isinstance(event, _rust.TrackUnpublished)
                and event.user_id == call_users[0].id
            ):
                break
        assert event.cause == models_pb2.TRACK_UNPUBLISH_REASON_USER_MUTED

    @pytest.mark.integration
    async def test_screen_share_is_published_and_unpublished(
        self,
        joined_call: _rust.Call,
        joining_call: _rust.Call,
        call_users: list[FullUserResponse],
    ):
        await joining_call.join(call_users[1].id)
        events = joining_call.sfu_events()
        track = _rust.LocalVideoTrack.vp8()

        await joined_call.publish_screen_share(track)
        async for event in events:
            if (
                isinstance(event, _rust.TrackPublished)
                and event.user_id == call_users[0].id
            ):
                break
        assert event.track_type == _rust.TrackType.SCREEN_SHARE

        await joined_call.stop_publish_screen_share(track)
        async for event in events:
            if (
                isinstance(event, _rust.TrackUnpublished)
                and event.user_id == call_users[0].id
            ):
                break
        assert event.track_type == _rust.TrackType.SCREEN_SHARE


@pytest.mark.integration
class TestCallEvents:
    async def test_calling_state_changed_to_joined(
        self, rust_client: _rust.Client, call_users: list[FullUserResponse]
    ):
        call = rust_client.call("default", str(uuid.uuid4()))
        events = call.client_events()

        await call.join(call_users[0].id)
        async for event in events:
            if (
                isinstance(event, _rust.CallingStateChanged)
                and event.state == _rust.CallingState.JOINED
            ):
                break
        await call.leave()

    async def test_participant_joined(
        self,
        joined_call: _rust.Call,
        joining_call: _rust.Call,
        call_id: str,
        call_users: list[FullUserResponse],
    ):
        events = joined_call.sfu_events()

        await joining_call.join(call_users[1].id)
        async for event in events:
            if (
                isinstance(event, _rust.ParticipantJoined)
                and event.participant.user_id == call_users[1].id
            ):
                break
        assert event.call_cid == f"default:{call_id}"
        participant = event.participant
        assert abs(participant.joined_at - time.time()) < 60
        assert participant.custom == {}
        assert participant.connection_quality in models_pb2.ConnectionQuality.values()
        assert participant.source == models_pb2.PARTICIPANT_SOURCE_WEBRTC_UNSPECIFIED

    async def test_events_end_when_call_is_left(
        self, rust_client: _rust.Client, call_users: list[FullUserResponse]
    ):
        call = rust_client.call("default", str(uuid.uuid4()))
        events = call.client_events()

        await call.join(call_users[0].id)
        await call.leave()
        received = [event async for event in events]

        assert isinstance(received[-1], _rust.CallingStateChanged)
        assert received[-1].state == _rust.CallingState.LEFT

    async def test_events_created_after_leave_are_empty(
        self, rust_client: _rust.Client, call_users: list[FullUserResponse]
    ):
        call = rust_client.call("default", str(uuid.uuid4()))
        await call.join(call_users[0].id)
        await call.leave()

        for events in (
            call.sfu_events(),
            call.coordinator_events(),
            call.client_events(),
        ):
            assert [event async for event in events] == []

    async def test_events_end_when_call_ends(
        self, client: Stream, joined_call: _rust.Call, call_id: str
    ):
        sfu_events = joined_call.sfu_events()
        client_events = joined_call.client_events()

        client.video.call("default", call_id).end()
        received = [event async for event in client_events]

        assert received[-1].state == _rust.CallingState.LEFT
        # The SFU stream ends too, also when the SFU `call_ended` never came.
        async for _ in sfu_events:
            pass

    async def test_track_published(
        self,
        joined_call: _rust.Call,
        joining_call: _rust.Call,
        call_users: list[FullUserResponse],
    ):
        await joining_call.join(call_users[1].id)
        events = joining_call.sfu_events()

        await joined_call.publish_audio(_rust.LocalAudioTrack())
        async for event in events:
            if (
                isinstance(event, _rust.TrackPublished)
                and event.user_id == call_users[0].id
            ):
                assert event.track_type == _rust.TrackType.AUDIO
                assert event.participant.user_id == call_users[0].id
                break

    async def test_coordinator_event(
        self,
        client: Stream,
        joined_call: _rust.Call,
        call_id: str,
        call_users: list[FullUserResponse],
    ):
        events = joined_call.coordinator_events()

        client.video.call("default", call_id).send_call_event(
            user_id=call_users[1].id, custom={"type": "test_event"}
        )

        async for event in events:
            if event.name == "custom":
                break
        assert isinstance(event, _rust.CoordinatorEvent)
        assert event.data["custom"]["type"] == "test_event"

    async def test_pins_changed(
        self,
        client: Stream,
        joined_call: _rust.Call,
        call_id: str,
        call_users: list[FullUserResponse],
    ):
        events = joined_call.sfu_events()
        session_id = await joined_call.session_id()

        client.video.call("default", call_id).video_pin(
            session_id=session_id, user_id=call_users[0].id
        )

        async for event in events:
            if isinstance(event, _rust.PinsChanged):
                break
        assert event.name == "pins_updated"
        assert [(pin.user_id, pin.session_id) for pin in event.pins] == [
            (call_users[0].id, session_id)
        ]

    async def test_call_grants_updated(
        self,
        client: Stream,
        joined_call: _rust.Call,
        call_id: str,
        call_users: list[FullUserResponse],
    ):
        events = joined_call.sfu_events()

        client.video.call("default", call_id).update_user_permissions(
            user_id=call_users[0].id, revoke_permissions=["send-audio"]
        )

        async for event in events:
            if isinstance(event, _rust.CallGrantsUpdated):
                break
        assert event.current_grants.can_publish_audio is False


@pytest.mark.integration
class TestCallParticipants:
    async def test_participants_include_joined_participant(
        self,
        joined_call: _rust.Call,
        joining_call: _rust.Call,
        call_users: list[FullUserResponse],
    ):
        events = joined_call.sfu_events()
        await joining_call.join(call_users[1].id)
        async for event in events:
            if isinstance(event, _rust.ParticipantJoined):
                break

        user_ids = {p.user_id for p in joined_call.participants()}
        assert {call_users[0].id, call_users[1].id} <= user_ids

    async def test_call_state(
        self, joined_call: _rust.Call, call_users: list[FullUserResponse]
    ):
        state = joined_call.call_state()

        assert call_users[0].id in {p.user_id for p in state.participants}
        assert "send-audio" in state.own_capabilities


@pytest.mark.integration
class TestCallMedia:
    async def test_tracks_end_when_call_is_left(
        self, rust_client: _rust.Client, call_users: list[FullUserResponse]
    ):
        call = rust_client.call("default", str(uuid.uuid4()))
        tracks = call.tracks()

        await call.join(call_users[0].id)
        await call.leave()

        assert [track async for track in tracks] == []

    async def test_receives_published_audio(
        self,
        published_audio: _rust.LocalAudioTrack,
        joining_call: _rust.Call,
        call_users: list[FullUserResponse],
    ):
        tracks = joining_call.tracks()
        await joining_call.join(call_users[1].id)
        await joining_call.update_subscriptions(AUDIO)

        async for track in tracks:
            if track.track_type == _rust.TrackType.AUDIO:
                break
        assert track.participant.user_id == call_users[0].id

        while True:
            frame = await track.next_pcm()
            if np.abs(frame.samples).max() > 1000:
                break
        assert frame.sample_rate == SAMPLE_RATE
        assert frame.samples.dtype == np.int16
        assert frame.pts is not None

    async def test_receives_published_video(
        self,
        published_video: _rust.LocalVideoTrack,
        joining_call: _rust.Call,
        call_users: list[FullUserResponse],
    ):
        tracks = joining_call.tracks()
        await joining_call.join(call_users[1].id)
        await joining_call.update_subscriptions(AUDIO_AND_VIDEO)

        async for track in tracks:
            if track.track_type == _rust.TrackType.VIDEO:
                break
        assert track.participant.user_id == call_users[0].id

        frame = await anext(track.video_frames())
        assert (frame.width, frame.height) == (VIDEO_WIDTH, VIDEO_HEIGHT)
        assert frame.data.dtype == np.uint8
        assert frame.data.size == VIDEO_WIDTH * VIDEO_HEIGHT * 3 // 2

    async def test_frame_streams_of_one_track_get_the_same_frames(
        self, remote_video: _rust.RemoteTrack
    ):
        first, second = remote_video.video_frames(), remote_video.video_frames()

        first_timestamps, second_timestamps = await asyncio.wait_for(
            asyncio.gather(rtp_timestamps(first, 10), rtp_timestamps(second, 10)),
            timeout=15,
        )

        assert first_timestamps == second_timestamps

    async def test_an_unread_frame_stream_gets_the_latest_frame(
        self, remote_video: _rust.RemoteTrack
    ):
        read, unread = remote_video.video_frames(), remote_video.video_frames()

        timestamps = await asyncio.wait_for(rtp_timestamps(read, 10), timeout=15)
        frame = await asyncio.wait_for(anext(unread), timeout=5)

        assert frame.rtp_timestamp >= timestamps[-1]

    async def test_a_cancelled_read_leaves_the_frame_stream_usable(
        self, remote_video: _rust.RemoteTrack
    ):
        frames = remote_video.video_frames()
        await asyncio.wait_for(anext(frames), timeout=10)

        with contextlib.suppress(asyncio.TimeoutError):
            await asyncio.wait_for(anext(frames), timeout=0.001)

        await asyncio.wait_for(anext(frames), timeout=5)

    async def test_a_new_frame_stream_gets_frames_after_the_old_one_is_dropped(
        self, remote_video: _rust.RemoteTrack
    ):
        frames = remote_video.video_frames()
        await asyncio.wait_for(anext(frames), timeout=10)
        del frames
        # Lets the decoding stop before the new stream starts it again.
        await asyncio.sleep(0.5)

        await asyncio.wait_for(anext(remote_video.video_frames()), timeout=10)

    async def test_a_frame_stream_keeps_the_track_subscribed(
        self,
        published_video: _rust.LocalVideoTrack,
        joining_call: _rust.Call,
        call_users: list[FullUserResponse],
    ):
        tracks = joining_call.tracks()
        await joining_call.join(call_users[1].id)
        await joining_call.update_subscriptions(AUDIO_AND_VIDEO)
        frames = (await anext(tracks)).video_frames()

        # 3 s of video; a dropped track is unsubscribed well before that.
        await asyncio.wait_for(rtp_timestamps(frames, 3 * VIDEO_FPS), timeout=15)

    async def test_frame_stream_ends_when_the_call_is_left(
        self, remote_video: _rust.RemoteTrack, joining_call: _rust.Call
    ):
        frames = remote_video.video_frames()
        await asyncio.wait_for(anext(frames), timeout=10)

        await joining_call.leave()

        await asyncio.wait_for(read_to_end(frames), timeout=10)

    async def test_track_dropped_while_muted_arrives_again_after_unmute(
        self,
        published_audio: _rust.LocalAudioTrack,
        joined_call: _rust.Call,
        joining_call: _rust.Call,
        call_users: list[FullUserResponse],
    ):
        events = joining_call.sfu_events()
        tracks = joining_call.tracks()
        await joining_call.join(call_users[1].id)
        await joining_call.update_subscriptions(AUDIO)
        track = await anext(tracks)

        await joined_call.mute_track(_rust.TrackType.AUDIO)
        async for event in events:
            if (
                isinstance(event, _rust.TrackUnpublished)
                and event.user_id == call_users[0].id
            ):
                break
        del track
        await joined_call.unmute_track(_rust.TrackType.AUDIO)

        track = await asyncio.wait_for(anext(tracks), timeout=15)
        assert track.participant.user_id == call_users[0].id
        while True:
            frame = await asyncio.wait_for(track.next_pcm(), timeout=15)
            if np.abs(frame.samples).max() > 1000:
                break
