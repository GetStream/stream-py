import contextlib
import logging
import os
import sys
import time
import uuid
from typing import Iterator

import getstream_rtc
import numpy as np
import pytest

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
        track = getstream_rtc.LocalAudioTrack()
        with pytest.raises(getstream_rtc.RtcError):
            await track.write_pcm(overflowing_samples, SAMPLE_RATE, 1)
        # Returns after the records sent before it are delivered.
        getstream_rtc.configure_logging(None, logging.NOTSET)

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
        track = getstream_rtc.LocalAudioTrack()
        write = track.write_pcm(overflowing_samples, SAMPLE_RATE, 1)
        started = time.time()
        # Holds the GIL, so the record cannot reach Python before this ends.
        while time.time() - started < 0.3:
            pass
        with pytest.raises(getstream_rtc.RtcError):
            await write
        getstream_rtc.configure_logging(None, logging.NOTSET)

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
        track = getstream_rtc.LocalAudioTrack()

        for _ in range(20):
            write = track.write_pcm(overflowing_samples, SAMPLE_RATE, 1)
            track.flush()
            with contextlib.suppress(getstream_rtc.RtcError):
                await write

    async def test_no_records_after_logging_is_stopped(
        self, caplog: pytest.LogCaptureFixture, overflowing_samples: np.ndarray
    ):
        caplog.set_level(logging.DEBUG, logger="getstream")
        getstream_rtc.configure_logging(None, logging.NOTSET)
        track = getstream_rtc.LocalAudioTrack()

        with pytest.raises(getstream_rtc.RtcError):
            await track.write_pcm(overflowing_samples, SAMPLE_RATE, 1)

        assert not [r for r in caplog.records if r.name.startswith("getstream.rtc")]

    @pytest.mark.integration
    async def test_log_bodies_logs_request_bodies(
        self, sdk_logs: pytest.LogCaptureFixture, call_users: list[FullUserResponse]
    ):
        client = getstream_rtc.Client(
            os.environ["STREAM_API_KEY"],
            os.environ["STREAM_API_SECRET"],
            log_bodies=True,
        )
        call = client.call("default", str(uuid.uuid4()))
        await call.join(call_users[0].id)
        await call.leave()
        getstream_rtc.configure_logging(None, logging.NOTSET)

        record = next(
            r for r in sdk_logs.records if r.getMessage() == "stream.http.request_body"
        )
        assert record.body

    @pytest.mark.integration
    async def test_third_party_records_default_to_warning(
        self,
        sdk_logs: pytest.LogCaptureFixture,
        rust_client: getstream_rtc.Client,
        call_users: list[FullUserResponse],
    ):
        call = rust_client.call("default", str(uuid.uuid4()))
        await call.join(call_users[0].id)
        await call.leave()
        getstream_rtc.configure_logging(None, logging.NOTSET)

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
        rust_client: getstream_rtc.Client,
        call_users: list[FullUserResponse],
    ):
        logger = logging.getLogger("getstream")
        getstream_rtc.configure_logging(logger, logging.DEBUG, logging.DEBUG)
        call = rust_client.call("default", str(uuid.uuid4()))
        await call.join(call_users[0].id)
        await call.leave()
        getstream_rtc.configure_logging(None, logging.NOTSET)

        assert [
            r
            for r in sdk_logs.records
            if hasattr(r, "rust_target")
            and not r.rust_target.startswith("getstream::")
            and r.levelno == logging.DEBUG
        ]
