import asyncio
import contextlib
import logging
import os
import sys
import time
import uuid
from typing import AsyncIterator, Iterator

import numpy as np
import pytest

from getstream import Stream, _native
from getstream.models import FullUserResponse
from getstream.version import VERSION

SAMPLE_RATE = 48000
FRAME_SAMPLES = SAMPLE_RATE // 50
VIDEO_WIDTH = 320
VIDEO_HEIGHT = 240
VIDEO_FPS = 15


@pytest.fixture
def native_client() -> _native.Client:
    return _native.Client(os.environ["STREAM_API_KEY"], os.environ["STREAM_API_SECRET"])


@pytest.fixture
def call_id() -> str:
    return str(uuid.uuid4())


@pytest.fixture
def sdk_logs(caplog: pytest.LogCaptureFixture) -> Iterator[pytest.LogCaptureFixture]:
    caplog.set_level(logging.DEBUG, logger="getstream")
    logger = logging.getLogger("getstream")
    _native.configure_logging(logger, logger.getEffectiveLevel())
    yield caplog
    _native.configure_logging(None, logging.NOTSET)


@pytest.fixture
def overflowing_samples() -> np.ndarray:
    return np.zeros(SAMPLE_RATE * 61, dtype=np.int16)


@pytest.fixture
def long_switch_interval() -> Iterator[None]:
    # A busy Python thread then keeps the GIL for up to one second.
    interval = sys.getswitchinterval()
    sys.setswitchinterval(1.0)
    yield
    sys.setswitchinterval(interval)


@pytest.fixture
async def joined_call(
    native_client: _native.Client,
    call_id: str,
    random_users: list[FullUserResponse],
) -> AsyncIterator[_native.Call]:
    call = native_client.call("default", call_id)
    await call.join(random_users[0].id)
    yield call
    await call.leave()


@pytest.fixture
async def joining_call(
    native_client: _native.Client,
    call_id: str,
    random_users: list[FullUserResponse],
) -> AsyncIterator[_native.Call]:
    call = native_client.call("default", call_id)
    yield call
    await call.leave()


@pytest.fixture
def tone() -> np.ndarray:
    t = np.arange(FRAME_SAMPLES) / SAMPLE_RATE
    return (np.sin(2 * np.pi * 440 * t) * 10000).astype(np.int16)


@pytest.fixture
async def published_audio(
    joined_call: _native.Call, tone: np.ndarray
) -> AsyncIterator[_native.LocalAudioTrack]:
    track = _native.LocalAudioTrack()
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
    joined_call: _native.Call,
) -> AsyncIterator[_native.LocalVideoTrack]:
    track = _native.LocalVideoTrack.vp9()
    await joined_call.publish_video(track)
    frame = np.full(VIDEO_WIDTH * VIDEO_HEIGHT * 3 // 2, 128, dtype=np.uint8)

    async def write_forever() -> None:
        while True:
            await track.write_i420(frame, VIDEO_WIDTH, VIDEO_HEIGHT, 1 / VIDEO_FPS)
            await asyncio.sleep(1 / VIDEO_FPS)

    task = asyncio.ensure_future(write_forever())
    yield track
    task.cancel()


class TestNativeModule:
    def test_version_matches_package(self):
        assert _native.__version__ == VERSION


class TestClient:
    def test_empty_api_key_raises(self):
        with pytest.raises(_native.Error):
            _native.Client("", "secret")

    def test_non_websocket_ws_url_raises(self):
        with pytest.raises(_native.Error, match="must use ws or wss"):
            _native.Client(
                "key", "secret", ws_url="https://video.stream-io-api.com/api/v2/connect"
            )


class TestLocalTracks:
    async def test_audio_queue_overflow_raises(self):
        track = _native.LocalAudioTrack()
        samples = np.zeros(SAMPLE_RATE * 61, dtype=np.int16)

        with pytest.raises(_native.RtcError, match="pcm queue overflow"):
            await track.write_pcm(samples, SAMPLE_RATE, 1)

    async def test_misaligned_samples_raise(self):
        track = _native.LocalAudioTrack()
        samples = np.frombuffer(memoryview(bytearray(1921))[1:], dtype=np.int16)

        with pytest.raises(ValueError, match="aligned"):
            await track.write_pcm(samples, SAMPLE_RATE, 1)

    async def test_odd_video_dimensions_raise(self):
        track = _native.LocalVideoTrack.vp9()
        frame = np.zeros(321 * 240 * 3 // 2, dtype=np.uint8)

        with pytest.raises(_native.RtcError, match="must be non-zero and even"):
            await track.write_i420(frame, 321, 240, 1 / VIDEO_FPS)


class TestLogging:
    async def test_sdk_events_reach_python_logging(
        self, sdk_logs: pytest.LogCaptureFixture, overflowing_samples: np.ndarray
    ):
        track = _native.LocalAudioTrack()
        with pytest.raises(_native.RtcError):
            await track.write_pcm(overflowing_samples, SAMPLE_RATE, 1)
        # Returns after the records sent before it are delivered.
        _native.configure_logging(None, logging.NOTSET)

        record = next(
            r
            for r in sdk_logs.records
            if r.getMessage() == "stream.rtc.audio.pcm_queue_overflow"
        )
        assert record.name == "getstream.rtc.tracks.local"
        assert record.levelno == logging.DEBUG
        assert record.rust_target == "getstream::rtc::tracks::local"
        assert record.dropped_samples > 0
        assert record.capacity_samples == SAMPLE_RATE * 60

    async def test_records_keep_the_time_of_the_rust_event(
        self,
        sdk_logs: pytest.LogCaptureFixture,
        overflowing_samples: np.ndarray,
        long_switch_interval: None,
    ):
        track = _native.LocalAudioTrack()
        write = track.write_pcm(overflowing_samples, SAMPLE_RATE, 1)
        started = time.time()
        # Holds the GIL, so the record cannot reach Python before this ends.
        while time.time() - started < 0.3:
            pass
        with pytest.raises(_native.RtcError):
            await write
        _native.configure_logging(None, logging.NOTSET)

        record = next(
            r
            for r in sdk_logs.records
            if r.getMessage() == "stream.rtc.audio.pcm_queue_overflow"
        )
        assert record.created < started + 0.1
        assert abs(record.msecs - (record.created % 1) * 1000) < 1

    async def test_flush_during_logged_overflow_does_not_hang(
        self, sdk_logs: pytest.LogCaptureFixture, overflowing_samples: np.ndarray
    ):
        track = _native.LocalAudioTrack()

        for _ in range(20):
            write = track.write_pcm(overflowing_samples, SAMPLE_RATE, 1)
            track.flush()
            with contextlib.suppress(_native.RtcError):
                await write

    async def test_no_records_after_logging_is_stopped(
        self, caplog: pytest.LogCaptureFixture, overflowing_samples: np.ndarray
    ):
        caplog.set_level(logging.DEBUG, logger="getstream")
        _native.configure_logging(None, logging.NOTSET)
        track = _native.LocalAudioTrack()

        with pytest.raises(_native.RtcError):
            await track.write_pcm(overflowing_samples, SAMPLE_RATE, 1)

        assert not [r for r in caplog.records if r.name.startswith("getstream.rtc")]

    @pytest.mark.integration
    async def test_log_bodies_logs_request_bodies(
        self, sdk_logs: pytest.LogCaptureFixture, random_user: FullUserResponse
    ):
        client = _native.Client(
            os.environ["STREAM_API_KEY"],
            os.environ["STREAM_API_SECRET"],
            log_bodies=True,
        )
        call = client.call("default", str(uuid.uuid4()))
        await call.join(random_user.id)
        await call.leave()
        _native.configure_logging(None, logging.NOTSET)

        record = next(
            r for r in sdk_logs.records if r.getMessage() == "stream.http.request_body"
        )
        assert record.body

    @pytest.mark.integration
    async def test_third_party_records_default_to_warning(
        self,
        sdk_logs: pytest.LogCaptureFixture,
        native_client: _native.Client,
        random_user: FullUserResponse,
    ):
        call = native_client.call("default", str(uuid.uuid4()))
        await call.join(random_user.id)
        await call.leave()
        _native.configure_logging(None, logging.NOTSET)

        assert not [
            r
            for r in sdk_logs.records
            if hasattr(r, "rust_target")
            and not r.rust_target.startswith("getstream::")
            and r.levelno < logging.WARNING
        ]

    @pytest.mark.integration
    async def test_third_party_level_can_be_lowered(
        self,
        sdk_logs: pytest.LogCaptureFixture,
        native_client: _native.Client,
        random_user: FullUserResponse,
    ):
        logger = logging.getLogger("getstream")
        _native.configure_logging(logger, logging.DEBUG, logging.DEBUG)
        call = native_client.call("default", str(uuid.uuid4()))
        await call.join(random_user.id)
        await call.leave()
        _native.configure_logging(None, logging.NOTSET)

        assert [
            r
            for r in sdk_logs.records
            if hasattr(r, "rust_target")
            and not r.rust_target.startswith("getstream::")
            and r.levelno == logging.DEBUG
        ]


@pytest.mark.integration
class TestCallJoin:
    async def test_join_and_leave(
        self, native_client: _native.Client, random_user: FullUserResponse
    ):
        call = native_client.call("default", str(uuid.uuid4()))

        await call.join(random_user.id)
        assert call.calling_state == _native.CallingState.JOINED
        assert await call.session_id()

        await call.leave()
        assert call.calling_state == _native.CallingState.LEFT

    async def test_join_with_wrong_secret_raises(self, random_user: FullUserResponse):
        client = _native.Client(os.environ["STREAM_API_KEY"], "wrong-secret")
        call = client.call("default", str(uuid.uuid4()))

        with pytest.raises(_native.RtcError, match="coordinator connection error"):
            await call.join(random_user.id)

    async def test_cancelled_join_allows_new_join(
        self, native_client: _native.Client, random_user: FullUserResponse
    ):
        call = native_client.call("default", str(uuid.uuid4()))

        join = call.join(random_user.id)
        await asyncio.sleep(0.1)
        join.cancel()
        with pytest.raises(asyncio.CancelledError):
            await join

        await call.join(random_user.id)
        assert call.calling_state == _native.CallingState.JOINED
        await call.leave()

    async def test_leave_during_join(
        self, native_client: _native.Client, random_user: FullUserResponse
    ):
        call = native_client.call("default", str(uuid.uuid4()))

        join = call.join(random_user.id)
        await asyncio.sleep(0.1)
        await call.leave()
        # A fast join can finish before the leave stops it.
        with contextlib.suppress(_native.RtcError):
            await join
        assert call.calling_state == _native.CallingState.LEFT

        await call.join(random_user.id)
        assert call.calling_state == _native.CallingState.JOINED
        await call.leave()

    async def test_join_during_leave(
        self, native_client: _native.Client, random_user: FullUserResponse
    ):
        call = native_client.call("default", str(uuid.uuid4()))
        await call.join(random_user.id)

        leave = call.leave()
        try:
            await call.join(random_user.id)
        except _native.RtcError as error:
            assert "shall be called only once" in str(error)
        await leave

        # The join failed while the leave ran (LEFT), or it ran after the
        # leave finished (JOINED).
        if call.calling_state == _native.CallingState.LEFT:
            await call.join(random_user.id)
        assert call.calling_state == _native.CallingState.JOINED
        await call.leave()


@pytest.mark.integration
class TestCallEvents:
    async def test_calling_state_changed_to_joined(
        self, native_client: _native.Client, random_user: FullUserResponse
    ):
        call = native_client.call("default", str(uuid.uuid4()))
        events = call.events()

        await call.join(random_user.id)
        async for event in events:
            if (
                isinstance(event, _native.CallingStateChanged)
                and event.state == _native.CallingState.JOINED
            ):
                break
        await call.leave()

    async def test_participant_joined(
        self,
        joined_call: _native.Call,
        joining_call: _native.Call,
        random_users: list[FullUserResponse],
    ):
        events = joined_call.events()

        await joining_call.join(random_users[1].id)
        async for event in events:
            if (
                isinstance(event, _native.ParticipantJoined)
                and event.participant.user_id == random_users[1].id
            ):
                break

    async def test_events_end_when_call_is_left(
        self, native_client: _native.Client, random_user: FullUserResponse
    ):
        call = native_client.call("default", str(uuid.uuid4()))
        events = call.events()

        await call.join(random_user.id)
        await call.leave()
        received = [event async for event in events]

        assert isinstance(received[-1], _native.CallingStateChanged)
        assert received[-1].state == _native.CallingState.LEFT

    async def test_events_created_after_leave_are_empty(
        self, native_client: _native.Client, random_user: FullUserResponse
    ):
        call = native_client.call("default", str(uuid.uuid4()))
        await call.join(random_user.id)
        await call.leave()

        assert [event async for event in call.events()] == []

    async def test_events_end_when_call_ends(
        self, client: Stream, joined_call: _native.Call, call_id: str
    ):
        events = joined_call.events()

        client.video.call("default", call_id).end()
        received = [event async for event in events]

        assert isinstance(received[-1], _native.CallEnded)

    async def test_track_published(
        self,
        joined_call: _native.Call,
        joining_call: _native.Call,
        random_users: list[FullUserResponse],
    ):
        await joining_call.join(random_users[1].id)
        events = joining_call.events()

        await joined_call.publish_audio(_native.LocalAudioTrack())
        async for event in events:
            if (
                isinstance(event, _native.TrackPublished)
                and event.user_id == random_users[0].id
            ):
                assert event.track_type == _native.TrackType.AUDIO
                break


@pytest.mark.integration
class TestCallParticipants:
    async def test_participants_include_joined_participant(
        self,
        joined_call: _native.Call,
        joining_call: _native.Call,
        random_users: list[FullUserResponse],
    ):
        events = joined_call.events()
        await joining_call.join(random_users[1].id)
        async for event in events:
            if isinstance(event, _native.ParticipantJoined):
                break

        user_ids = {p.user_id for p in joined_call.participants()}
        assert {random_users[0].id, random_users[1].id} <= user_ids

    async def test_call_state(
        self, joined_call: _native.Call, random_users: list[FullUserResponse]
    ):
        state = joined_call.call_state()

        assert random_users[0].id in {p.user_id for p in state.participants}
        assert "send-audio" in state.own_capabilities


@pytest.mark.integration
class TestCallMedia:
    async def test_tracks_end_when_call_is_left(
        self, native_client: _native.Client, random_user: FullUserResponse
    ):
        call = native_client.call("default", str(uuid.uuid4()))
        tracks = call.tracks()

        await call.join(random_user.id)
        await call.leave()

        assert [track async for track in tracks] == []

    async def test_receives_published_audio(
        self,
        published_audio: _native.LocalAudioTrack,
        joining_call: _native.Call,
        random_users: list[FullUserResponse],
    ):
        tracks = joining_call.tracks()
        await joining_call.join(random_users[1].id)
        await joining_call.update_subscriptions(audio=True)

        async for track in tracks:
            if track.track_type == _native.TrackType.AUDIO:
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
        published_video: _native.LocalVideoTrack,
        joining_call: _native.Call,
        random_users: list[FullUserResponse],
    ):
        tracks = joining_call.tracks()
        await joining_call.join(random_users[1].id)
        await joining_call.update_subscriptions(audio=True, video=True)

        async for track in tracks:
            if track.track_type == _native.TrackType.VIDEO:
                break
        assert track.participant.user_id == random_users[0].id

        frame = await track.next_video_frame()
        assert (frame.width, frame.height) == (VIDEO_WIDTH, VIDEO_HEIGHT)
        assert frame.data.dtype == np.uint8
        assert frame.data.size == VIDEO_WIDTH * VIDEO_HEIGHT * 3 // 2
