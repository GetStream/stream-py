"""Shared helpers for live, credential-gated RTC behavioral tests.

These tests talk to a real Stream SFU. They skip when STREAM_API_KEY /
STREAM_API_SECRET are missing. Nothing is mocked.
"""

from __future__ import annotations

import asyncio
import os
import subprocess
import sys
import time
import uuid
from fractions import Fraction
from contextlib import asynccontextmanager
from typing import Any, Callable

import numpy as np
import pytest
import pytest_asyncio

pytest.importorskip("getstream_rtc_core")

from getstream import AsyncStream
from getstream.models import CallRequest, MemberRequest, UserRequest
from getstream.video import rtc
from getstream.video.rtc.audio_track import AudioStreamTrack
from getstream.video.rtc.connection_utils import ConnectionState
from getstream.video.rtc.media import MediaStreamError
from getstream.video.rtc.pb.stream.video.sfu.models.models_pb2 import (
    TRACK_TYPE_AUDIO,
    TRACK_TYPE_VIDEO,
)
from getstream.video.rtc.track_util import AudioFormat, PcmData
from getstream.video.rtc.tracks import SubscriptionConfig, TrackSubscriptionConfig
from tests.conftest import skip_on_rate_limit

SAMPLE_RATE = 48_000
FRAME_MS = 20
FRAME_SAMPLES = SAMPLE_RATE * FRAME_MS // 1000
TONE_HZ = 440.0
TONE_AMP = 12_000.0
LOUD_TONE_AMP = 26_000.0
QUIET_SPEECH_AMP = 2_000.0
NON_SILENT_RMS = 200.0
MEDIA_TIMEOUT = 45.0
VIDEO_WIDTH = 320
VIDEO_HEIGHT = 240


def require_stream_credentials() -> None:
    if not os.environ.get("STREAM_API_KEY") or not os.environ.get("STREAM_API_SECRET"):
        pytest.skip("STREAM_API_KEY and STREAM_API_SECRET are required")


def unique_id(prefix: str) -> str:
    return f"{prefix}-{uuid.uuid4()}"


def audio_only_config() -> SubscriptionConfig:
    return SubscriptionConfig(
        default=TrackSubscriptionConfig(track_types=[TRACK_TYPE_AUDIO])
    )


def audio_video_config() -> SubscriptionConfig:
    return SubscriptionConfig(
        default=TrackSubscriptionConfig(
            track_types=[TRACK_TYPE_AUDIO, TRACK_TYPE_VIDEO]
        )
    )


def sine_pcm(
    *,
    n: int,
    count: int,
    amp: float,
    freq: float = TONE_HZ,
    sample_rate: int = SAMPLE_RATE,
) -> PcmData:
    t = (n + np.arange(count, dtype=np.float64)) / sample_rate
    samples = (amp * np.sin(2.0 * np.pi * freq * t)).astype(np.int16)
    return PcmData(
        samples=samples,
        sample_rate=sample_rate,
        format=AudioFormat.S16,
        channels=1,
    )


def pcm_rms(pcm: PcmData) -> float:
    samples = np.asarray(pcm.samples, dtype=np.float64).ravel()
    if samples.size == 0:
        return 0.0
    return float(np.sqrt(np.mean(samples * samples)))


def process_rss_bytes() -> int:
    pid = os.getpid()
    if sys.platform == "darwin":
        out = subprocess.check_output(
            ["ps", "-o", "rss=", "-p", str(pid)], text=True
        ).strip()
        return int(out) * 1024
    with open(f"/proc/{pid}/status", encoding="utf-8") as fh:
        for line in fh:
            if line.startswith("VmRSS:"):
                return int(line.split()[1]) * 1024
    raise RuntimeError("unable to read process RSS")


class EventLog:
    """Collect ConnectionManager events and wait for a matching payload."""

    def __init__(self) -> None:
        self.items: list[tuple[str, tuple[Any, ...]]] = []
        self._changed = asyncio.Event()

    def bind(self, connection, event_name: str) -> None:
        def handler(*args: Any) -> None:
            self.items.append((event_name, args))
            self._changed.set()

        connection.on(event_name, handler)

    def payloads(self, event_name: str) -> list[tuple[Any, ...]]:
        return [args for name, args in self.items if name == event_name]

    async def wait_for(
        self,
        predicate: Callable[[], bool],
        timeout: float,
        message: str = "event condition not met",
    ) -> None:
        deadline = time.monotonic() + timeout
        while time.monotonic() < deadline:
            if predicate():
                return
            remaining = deadline - time.monotonic()
            if remaining <= 0:
                break
            self._changed.clear()
            if predicate():
                return
            try:
                await asyncio.wait_for(self._changed.wait(), timeout=remaining)
            except asyncio.TimeoutError:
                break
        raise TimeoutError(message)


class SolidColorVideoTrack:
    """Duck-typed video source: a solid BT.601 limited-range blue I420 frame."""

    kind = "video"

    def __init__(
        self, width: int = VIDEO_WIDTH, height: int = VIDEO_HEIGHT, fps: float = 10.0
    ) -> None:
        self._id = str(uuid.uuid4())
        self._ready_state = "live"
        self.width = width
        self.height = height
        self._interval = 1.0 / fps
        y = np.full((height, width), 41, dtype=np.uint8)
        u = np.full((height // 4, width), 240, dtype=np.uint8)
        v = np.full((height // 4, width), 110, dtype=np.uint8)
        self._i420 = np.concatenate([y, u, v], axis=0)

    @property
    def id(self) -> str:
        return self._id

    @property
    def readyState(self) -> str:
        return self._ready_state

    def stop(self) -> None:
        self._ready_state = "ended"

    async def recv(self):
        import av

        if self._ready_state != "live":
            raise MediaStreamError("Track is ended")
        await asyncio.sleep(self._interval)
        frame = av.VideoFrame.from_ndarray(self._i420, format="yuv420p")
        frame.pts = 0
        frame.time_base = Fraction(1, 1000)
        return frame


async def feed_tone(
    track: AudioStreamTrack,
    stop: asyncio.Event,
    *,
    amp: float = TONE_AMP,
    speech: bool = False,
) -> None:
    """Write a continuous 440 Hz tone (or speech-shaped bursts) until stopped."""
    n = 0
    frame_index = 0
    while not stop.is_set() and track.readyState == "live":
        current_amp = amp
        if speech:
            current_amp = QUIET_SPEECH_AMP if frame_index < 25 else LOUD_TONE_AMP
            frame_index = (frame_index + 1) % 85
        await track.write(sine_pcm(n=n, count=FRAME_SAMPLES, amp=current_amp))
        n += FRAME_SAMPLES
        try:
            await asyncio.wait_for(stop.wait(), timeout=FRAME_MS / 1000)
        except asyncio.TimeoutError:
            pass


class AudioPublication:
    """Live published audio track plus a handle to stop the tone feeder."""

    def __init__(self, track: AudioStreamTrack, stop: asyncio.Event) -> None:
        self.track = track
        self._stop = stop

    def stop_feeding(self) -> None:
        self._stop.set()


@asynccontextmanager
async def publishing_audio(connection, *, amp: float = TONE_AMP, speech: bool = False):
    track = AudioStreamTrack(sample_rate=SAMPLE_RATE, channels=1, format="s16")
    stop = asyncio.Event()
    feeder = asyncio.create_task(
        feed_tone(track, stop, amp=amp, speech=speech), name="live-tone-feeder"
    )
    await connection.add_tracks(audio=track)
    try:
        yield AudioPublication(track, stop)
    finally:
        stop.set()
        feeder.cancel()
        try:
            await feeder
        except asyncio.CancelledError:
            pass
        track.stop()


@asynccontextmanager
async def publishing_video(connection):
    track = SolidColorVideoTrack()
    await connection.add_tracks(video=track)
    try:
        yield track
    finally:
        track.stop()


def rtc_session(connection):
    session = connection._rtc_session
    if session is None:
        pytest.skip("RTC session is not attached")
    return session


async def apply_subscriptions(connection, *, audio: bool = True, video: bool = False):
    kwargs = {"audio": audio, "video": video, "screen_share": False}
    if video:
        kwargs["video_width"] = 1280
        kwargs["video_height"] = 720
    await rtc_session(connection).update_subscriptions(**kwargs)


async def wait_for_state(
    connection, state: ConnectionState, timeout: float = 30.0
) -> None:
    if connection.connection_state == state:
        return
    got = asyncio.Event()

    def on_state(payload: dict, *args: Any) -> None:
        if payload.get("new") == state:
            got.set()

    connection.on("connection.state_changed", on_state)
    if connection.connection_state == state:
        return
    await asyncio.wait_for(got.wait(), timeout=timeout)


async def wait_for_non_silent_audio(
    events: EventLog, timeout: float = MEDIA_TIMEOUT
) -> PcmData:
    def found() -> bool:
        for args in events.payloads("audio"):
            if args and pcm_rms(args[0]) >= NON_SILENT_RMS:
                return True
        return False

    await events.wait_for(
        found, timeout, "did not receive non-silent remote audio"
    )
    for args in events.payloads("audio"):
        if args and pcm_rms(args[0]) >= NON_SILENT_RMS:
            return args[0]
    raise TimeoutError("did not receive non-silent remote audio")


@pytest_asyncio.fixture
async def live_call():
    require_stream_credentials()
    client = AsyncStream(timeout=15.0)
    user_ids = [unique_id("py-live") for _ in range(3)]
    await client.upsert_users(*[UserRequest(id=uid) for uid in user_ids])
    call = client.video.call("default", unique_id("py-live-call"))
    await call.get_or_create(
        data=CallRequest(
            created_by_id=user_ids[0],
            members=[MemberRequest(user_id=uid) for uid in user_ids],
        )
    )
    try:
        yield call, user_ids
    finally:
        try:
            await call.delete(hard=True)
        except Exception:
            pass
        try:
            await client.delete_users(
                user_ids=user_ids, user="hard", conversations="hard", messages="hard"
            )
        except Exception:
            pass


__all__ = [
    "AudioPublication",
    "EventLog",
    "LOUD_TONE_AMP",
    "MEDIA_TIMEOUT",
    "SAMPLE_RATE",
    "SolidColorVideoTrack",
    "TONE_AMP",
    "apply_subscriptions",
    "audio_only_config",
    "audio_video_config",
    "feed_tone",
    "live_call",
    "pcm_rms",
    "process_rss_bytes",
    "publishing_audio",
    "publishing_video",
    "require_stream_credentials",
    "rtc",
    "rtc_session",
    "skip_on_rate_limit",
    "unique_id",
    "wait_for_non_silent_audio",
    "wait_for_state",
]
