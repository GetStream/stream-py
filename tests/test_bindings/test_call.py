import asyncio
import contextlib
import os
import uuid
from typing import AsyncIterator

import numpy as np
import pytest

from getstream import Stream, _rust
from getstream.models import FullUserResponse

SAMPLE_RATE = 48000
FRAME_SAMPLES = SAMPLE_RATE // 50
VIDEO_WIDTH = 320
VIDEO_HEIGHT = 240
VIDEO_FPS = 15


@pytest.fixture
def call_id() -> str:
    return str(uuid.uuid4())


@pytest.fixture
async def joined_call(
    rust_client: _rust.Client,
    call_id: str,
    random_users: list[FullUserResponse],
) -> AsyncIterator[_rust.Call]:
    call = rust_client.call("default", call_id)
    await call.join(random_users[0].id)
    yield call
    await call.leave()


@pytest.fixture
async def joining_call(
    rust_client: _rust.Client,
    call_id: str,
    random_users: list[FullUserResponse],
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

    task = asyncio.ensure_future(write_forever())
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

    task = asyncio.ensure_future(write_forever())
    yield track
    task.cancel()


@pytest.mark.integration
class TestCallJoin:
    async def test_join_and_leave(
        self, rust_client: _rust.Client, random_user: FullUserResponse
    ):
        call = rust_client.call("default", str(uuid.uuid4()))

        await call.join(random_user.id)
        assert call.calling_state == _rust.CallingState.JOINED
        assert await call.session_id()

        await call.leave()
        assert call.calling_state == _rust.CallingState.LEFT

    async def test_join_with_wrong_secret_raises(self, random_user: FullUserResponse):
        client = _rust.Client(os.environ["STREAM_API_KEY"], "wrong-secret")
        call = client.call("default", str(uuid.uuid4()))

        with pytest.raises(_rust.RtcError, match="coordinator connection error"):
            await call.join(random_user.id)

    async def test_cancelled_join_allows_new_join(
        self, rust_client: _rust.Client, random_user: FullUserResponse
    ):
        call = rust_client.call("default", str(uuid.uuid4()))

        join = call.join(random_user.id)
        await asyncio.sleep(0.1)
        join.cancel()
        with pytest.raises(asyncio.CancelledError):
            await join

        await call.join(random_user.id)
        assert call.calling_state == _rust.CallingState.JOINED
        await call.leave()

    async def test_leave_during_join(
        self, rust_client: _rust.Client, random_user: FullUserResponse
    ):
        call = rust_client.call("default", str(uuid.uuid4()))

        join = call.join(random_user.id)
        await asyncio.sleep(0.1)
        await call.leave()
        # A fast join can finish before the leave stops it.
        with contextlib.suppress(_rust.RtcError):
            await join
        assert call.calling_state == _rust.CallingState.LEFT

        await call.join(random_user.id)
        assert call.calling_state == _rust.CallingState.JOINED
        await call.leave()

    async def test_join_during_leave(
        self, rust_client: _rust.Client, random_user: FullUserResponse
    ):
        call = rust_client.call("default", str(uuid.uuid4()))
        await call.join(random_user.id)

        leave = call.leave()
        try:
            await call.join(random_user.id)
        except _rust.RtcError as error:
            assert "shall be called only once" in str(error)
        await leave

        # The join failed while the leave ran (LEFT), or it ran after the
        # leave finished (JOINED).
        if call.calling_state == _rust.CallingState.LEFT:
            await call.join(random_user.id)
        assert call.calling_state == _rust.CallingState.JOINED
        await call.leave()


@pytest.mark.integration
class TestCallEvents:
    async def test_calling_state_changed_to_joined(
        self, rust_client: _rust.Client, random_user: FullUserResponse
    ):
        call = rust_client.call("default", str(uuid.uuid4()))
        events = call.events()

        await call.join(random_user.id)
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
        random_users: list[FullUserResponse],
    ):
        events = joined_call.events()

        await joining_call.join(random_users[1].id)
        async for event in events:
            if (
                isinstance(event, _rust.ParticipantJoined)
                and event.participant.user_id == random_users[1].id
            ):
                break

    async def test_events_end_when_call_is_left(
        self, rust_client: _rust.Client, random_user: FullUserResponse
    ):
        call = rust_client.call("default", str(uuid.uuid4()))
        events = call.events()

        await call.join(random_user.id)
        await call.leave()
        received = [event async for event in events]

        assert isinstance(received[-1], _rust.CallingStateChanged)
        assert received[-1].state == _rust.CallingState.LEFT

    async def test_events_created_after_leave_are_empty(
        self, rust_client: _rust.Client, random_user: FullUserResponse
    ):
        call = rust_client.call("default", str(uuid.uuid4()))
        await call.join(random_user.id)
        await call.leave()

        assert [event async for event in call.events()] == []

    async def test_events_end_when_call_ends(
        self, client: Stream, joined_call: _rust.Call, call_id: str
    ):
        events = joined_call.events()

        client.video.call("default", call_id).end()
        received = [event async for event in events]

        assert isinstance(received[-1], _rust.CallEnded)

    async def test_track_published(
        self,
        joined_call: _rust.Call,
        joining_call: _rust.Call,
        random_users: list[FullUserResponse],
    ):
        await joining_call.join(random_users[1].id)
        events = joining_call.events()

        await joined_call.publish_audio(_rust.LocalAudioTrack())
        async for event in events:
            if (
                isinstance(event, _rust.TrackPublished)
                and event.user_id == random_users[0].id
            ):
                assert event.track_type == _rust.TrackType.AUDIO
                break


@pytest.mark.integration
class TestCallParticipants:
    async def test_participants_include_joined_participant(
        self,
        joined_call: _rust.Call,
        joining_call: _rust.Call,
        random_users: list[FullUserResponse],
    ):
        events = joined_call.events()
        await joining_call.join(random_users[1].id)
        async for event in events:
            if isinstance(event, _rust.ParticipantJoined):
                break

        user_ids = {p.user_id for p in joined_call.participants()}
        assert {random_users[0].id, random_users[1].id} <= user_ids

    async def test_call_state(
        self, joined_call: _rust.Call, random_users: list[FullUserResponse]
    ):
        state = joined_call.call_state()

        assert random_users[0].id in {p.user_id for p in state.participants}
        assert "send-audio" in state.own_capabilities


@pytest.mark.integration
class TestCallMedia:
    async def test_tracks_end_when_call_is_left(
        self, rust_client: _rust.Client, random_user: FullUserResponse
    ):
        call = rust_client.call("default", str(uuid.uuid4()))
        tracks = call.tracks()

        await call.join(random_user.id)
        await call.leave()

        assert [track async for track in tracks] == []

    async def test_receives_published_audio(
        self,
        published_audio: _rust.LocalAudioTrack,
        joining_call: _rust.Call,
        random_users: list[FullUserResponse],
    ):
        tracks = joining_call.tracks()
        await joining_call.join(random_users[1].id)
        await joining_call.update_subscriptions(audio=True)

        async for track in tracks:
            if track.track_type == _rust.TrackType.AUDIO:
                break
        assert track.participant.user_id == random_users[0].id

        while True:
            frame = await track.next_pcm()
            if np.abs(frame.samples).max() > 1000:
                break
        assert frame.sample_rate == SAMPLE_RATE
        assert frame.samples.dtype == np.int16

    async def test_receives_published_video(
        self,
        published_video: _rust.LocalVideoTrack,
        joining_call: _rust.Call,
        random_users: list[FullUserResponse],
    ):
        tracks = joining_call.tracks()
        await joining_call.join(random_users[1].id)
        await joining_call.update_subscriptions(audio=True, video=True)

        async for track in tracks:
            if track.track_type == _rust.TrackType.VIDEO:
                break
        assert track.participant.user_id == random_users[0].id

        frame = await track.next_video_frame()
        assert (frame.width, frame.height) == (VIDEO_WIDTH, VIDEO_HEIGHT)
        assert frame.data.dtype == np.uint8
        assert frame.data.size == VIDEO_WIDTH * VIDEO_HEIGHT * 3 // 2
