import contextlib
import logging
import os
import sys
import time
import uuid
from typing import Iterator

import numpy as np
import pytest

from getstream import _rust
from getstream.models import FullUserResponse

SAMPLE_RATE = 48000


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


class TestLogging:
    async def test_sdk_events_reach_python_logging(
        self, sdk_logs: pytest.LogCaptureFixture, overflowing_samples: np.ndarray
    ):
        track = _rust.LocalAudioTrack()
        with pytest.raises(_rust.RtcError):
            await track.write_pcm(overflowing_samples, SAMPLE_RATE, 1)
        # Returns after the records sent before it are delivered.
        _rust.configure_logging(None, logging.NOTSET)

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
        track = _rust.LocalAudioTrack()
        write = track.write_pcm(overflowing_samples, SAMPLE_RATE, 1)
        started = time.time()
        # Holds the GIL, so the record cannot reach Python before this ends.
        while time.time() - started < 0.3:
            pass
        with pytest.raises(_rust.RtcError):
            await write
        _rust.configure_logging(None, logging.NOTSET)

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
        track = _rust.LocalAudioTrack()

        for _ in range(20):
            write = track.write_pcm(overflowing_samples, SAMPLE_RATE, 1)
            track.flush()
            with contextlib.suppress(_rust.RtcError):
                await write

    async def test_no_records_after_logging_is_stopped(
        self, caplog: pytest.LogCaptureFixture, overflowing_samples: np.ndarray
    ):
        caplog.set_level(logging.DEBUG, logger="getstream")
        _rust.configure_logging(None, logging.NOTSET)
        track = _rust.LocalAudioTrack()

        with pytest.raises(_rust.RtcError):
            await track.write_pcm(overflowing_samples, SAMPLE_RATE, 1)

        assert not [r for r in caplog.records if r.name.startswith("getstream.rtc")]

    @pytest.mark.integration
    async def test_log_bodies_logs_request_bodies(
        self, sdk_logs: pytest.LogCaptureFixture, random_user: FullUserResponse
    ):
        client = _rust.Client(
            os.environ["STREAM_API_KEY"],
            os.environ["STREAM_API_SECRET"],
            log_bodies=True,
        )
        call = client.call("default", str(uuid.uuid4()))
        await call.join(random_user.id)
        await call.leave()
        _rust.configure_logging(None, logging.NOTSET)

        record = next(
            r for r in sdk_logs.records if r.getMessage() == "stream.http.request_body"
        )
        assert record.body

    @pytest.mark.integration
    async def test_third_party_records_default_to_warning(
        self,
        sdk_logs: pytest.LogCaptureFixture,
        rust_client: _rust.Client,
        random_user: FullUserResponse,
    ):
        call = rust_client.call("default", str(uuid.uuid4()))
        await call.join(random_user.id)
        await call.leave()
        _rust.configure_logging(None, logging.NOTSET)

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
        rust_client: _rust.Client,
        random_user: FullUserResponse,
    ):
        logger = logging.getLogger("getstream")
        _rust.configure_logging(logger, logging.DEBUG, logging.DEBUG)
        call = rust_client.call("default", str(uuid.uuid4()))
        await call.join(random_user.id)
        await call.leave()
        _rust.configure_logging(None, logging.NOTSET)

        assert [
            r
            for r in sdk_logs.records
            if hasattr(r, "rust_target")
            and not r.rust_target.startswith("getstream::")
            and r.levelno == logging.DEBUG
        ]
