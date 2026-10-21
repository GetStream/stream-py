import contextlib
import logging
import os
import sys
import threading
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


@pytest.fixture
def small_track() -> getstream_rtc.LocalAudioTrack:
    return getstream_rtc.LocalAudioTrack(pcm_queue_capacity=0.05)


@pytest.fixture
def overflowing_chunk() -> np.ndarray:
    # Twice the capacity of `small_track`: each write overflows and logs
    # `stream.rtc.audio.pcm_queue_overflow` once.
    return np.zeros(SAMPLE_RATE // 10, dtype=np.int16)


class BlockingHandler(logging.Handler):
    """Blocks the thread that handles the first audio overflow record until
    `release` is set."""

    def __init__(self) -> None:
        super().__init__()
        self.entered = threading.Event()
        self.release = threading.Event()

    def emit(self, record: logging.LogRecord) -> None:
        if (
            record.getMessage() == "stream.rtc.audio.pcm_queue_overflow"
            and not self.entered.is_set()
        ):
            self.entered.set()
            self.release.wait()


@pytest.fixture
def blocking_handler() -> Iterator[BlockingHandler]:
    logger = logging.getLogger("getstream")
    handler = BlockingHandler()
    logger.addHandler(handler)
    yield handler
    handler.release.set()
    logger.removeHandler(handler)


class FlushingHandler(logging.Handler):
    """Calls `_flush()` on the thread that handles the records."""

    def __init__(self) -> None:
        super().__init__()
        self.flushed = threading.Event()

    def emit(self, record: logging.LogRecord) -> None:
        getstream_rtc.logging._flush()
        self.flushed.set()


@pytest.fixture
def flushing_handler() -> Iterator[FlushingHandler]:
    logger = logging.getLogger("getstream")
    handler = FlushingHandler()
    logger.addHandler(handler)
    yield handler
    logger.removeHandler(handler)


class FailOnce(logging.Filter):
    """Raises for the first record."""

    def __init__(self) -> None:
        super().__init__()
        self.failed = False

    def filter(self, record: logging.LogRecord) -> bool:
        if not self.failed:
            self.failed = True
            raise ValueError("a failing filter")
        return True


@pytest.fixture
def failing_filter() -> Iterator[None]:
    # `handle_record` calls `handle()` of the child logger, which applies only
    # its own filters.
    logger = logging.getLogger("getstream.rtc.tracks.local")
    log_filter = FailOnce()
    logger.addFilter(log_filter)
    yield
    logger.removeFilter(log_filter)


class ExitOnce(logging.Handler):
    """Raises `SystemExit` for the first audio overflow record, which ends the
    thread that handles it."""

    def __init__(self) -> None:
        super().__init__()
        self.raised = threading.Event()

    def emit(self, record: logging.LogRecord) -> None:
        if (
            record.getMessage() == "stream.rtc.audio.pcm_queue_overflow"
            and not self.raised.is_set()
        ):
            self.raised.set()
            raise SystemExit


@pytest.fixture
def exiting_handler() -> Iterator[ExitOnce]:
    logger = logging.getLogger("getstream")
    handler = ExitOnce()
    logger.addHandler(handler)
    yield handler
    logger.removeHandler(handler)


class TestLogging:
    async def test_sdk_events_reach_python_logging(
        self, sdk_logs: pytest.LogCaptureFixture, overflowing_samples: np.ndarray
    ) -> None:
        track = getstream_rtc.LocalAudioTrack()
        with pytest.raises(getstream_rtc.RtcError):
            await track.write_pcm(overflowing_samples, SAMPLE_RATE, 1)
        getstream_rtc.logging._flush()

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
    ) -> None:
        track = getstream_rtc.LocalAudioTrack()
        write = track.write_pcm(overflowing_samples, SAMPLE_RATE, 1)
        started = time.time()
        # Holds the GIL, so the record cannot reach Python before this ends.
        while time.time() - started < 0.3:
            pass
        with pytest.raises(getstream_rtc.RtcError):
            await write
        getstream_rtc.logging._flush()

        record = next(
            r
            for r in sdk_logs.records
            if r.getMessage() == "stream.rtc.audio.pcm_queue_overflow"
        )
        assert record.created < started + 0.1
        assert abs(record.msecs - (record.created % 1) * 1000) < 1

    async def test_flush_during_logged_overflow_does_not_hang(
        self, sdk_logs: pytest.LogCaptureFixture, overflowing_samples: np.ndarray
    ) -> None:
        track = getstream_rtc.LocalAudioTrack()

        for _ in range(20):
            write = track.write_pcm(overflowing_samples, SAMPLE_RATE, 1)
            track.flush()
            with contextlib.suppress(getstream_rtc.RtcError):
                await write

    async def test_no_records_after_logging_is_stopped(
        self, sdk_logs: pytest.LogCaptureFixture, overflowing_samples: np.ndarray
    ) -> None:
        getstream_rtc.configure_logging(None, logging.NOTSET)
        track = getstream_rtc.LocalAudioTrack()

        with pytest.raises(getstream_rtc.RtcError):
            await track.write_pcm(overflowing_samples, SAMPLE_RATE, 1)
        getstream_rtc.logging._flush()

        assert not [r for r in sdk_logs.records if r.name.startswith("getstream.rtc")]

    async def test_records_come_from_the_logging_thread(
        self,
        sdk_logs: pytest.LogCaptureFixture,
        small_track: getstream_rtc.LocalAudioTrack,
        overflowing_chunk: np.ndarray,
    ) -> None:
        with contextlib.suppress(getstream_rtc.PcmQueueOverflowError):
            await small_track.write_pcm(overflowing_chunk, SAMPLE_RATE, 1)
        getstream_rtc.logging._flush()

        record = next(
            r
            for r in sdk_logs.records
            if r.getMessage() == "stream.rtc.audio.pcm_queue_overflow"
        )
        assert record.threadName == "getstream-logging"

    async def test_configure_logging_returns_while_a_handler_runs(
        self,
        sdk_logs: pytest.LogCaptureFixture,
        blocking_handler: BlockingHandler,
        small_track: getstream_rtc.LocalAudioTrack,
        overflowing_chunk: np.ndarray,
    ) -> None:
        with contextlib.suppress(getstream_rtc.PcmQueueOverflowError):
            await small_track.write_pcm(overflowing_chunk, SAMPLE_RATE, 1)
        assert blocking_handler.entered.wait(timeout=5)

        configure = threading.Thread(
            target=getstream_rtc.configure_logging, args=(None, logging.NOTSET)
        )
        configure.start()
        configure.join(timeout=1)

        assert not configure.is_alive()

    async def test_flush_returns_on_the_logging_thread(
        self,
        sdk_logs: pytest.LogCaptureFixture,
        flushing_handler: FlushingHandler,
        small_track: getstream_rtc.LocalAudioTrack,
        overflowing_chunk: np.ndarray,
    ) -> None:
        with contextlib.suppress(getstream_rtc.PcmQueueOverflowError):
            await small_track.write_pcm(overflowing_chunk, SAMPLE_RATE, 1)

        assert flushing_handler.flushed.wait(timeout=5)

    async def test_records_dropped_at_the_end_are_reported(
        self,
        sdk_logs: pytest.LogCaptureFixture,
        blocking_handler: BlockingHandler,
        small_track: getstream_rtc.LocalAudioTrack,
        overflowing_chunk: np.ndarray,
    ) -> None:
        # While the handler blocks the logging thread, the queue (1024) and one
        # batch (256) fill up, and the last records are dropped.
        for _ in range(1500):
            with contextlib.suppress(getstream_rtc.PcmQueueOverflowError):
                await small_track.write_pcm(overflowing_chunk, SAMPLE_RATE, 1)
        blocking_handler.release.set()
        getstream_rtc.logging._flush()

        dropped = [
            r
            for r in sdk_logs.records
            if r.getMessage() == "stream.rust.log_records_dropped"
        ]
        assert dropped
        assert dropped[0].dropped > 0

    async def test_records_after_a_failing_filter_are_delivered(
        self,
        sdk_logs: pytest.LogCaptureFixture,
        failing_filter: None,
        small_track: getstream_rtc.LocalAudioTrack,
        overflowing_chunk: np.ndarray,
    ) -> None:
        for _ in range(2):
            with contextlib.suppress(getstream_rtc.PcmQueueOverflowError):
                await small_track.write_pcm(overflowing_chunk, SAMPLE_RATE, 1)
        getstream_rtc.logging._flush()

        assert sdk_logs.messages.count("stream.rtc.audio.pcm_queue_overflow") == 1

    async def test_records_are_delivered_after_logging_is_enabled_again(
        self,
        sdk_logs: pytest.LogCaptureFixture,
        small_track: getstream_rtc.LocalAudioTrack,
        overflowing_chunk: np.ndarray,
    ) -> None:
        getstream_rtc.configure_logging(None, logging.NOTSET)
        getstream_rtc.configure_logging(logging.getLogger("getstream"), logging.DEBUG)

        with contextlib.suppress(getstream_rtc.PcmQueueOverflowError):
            await small_track.write_pcm(overflowing_chunk, SAMPLE_RATE, 1)
        getstream_rtc.logging._flush()

        assert "stream.rtc.audio.pcm_queue_overflow" in sdk_logs.messages

    @pytest.mark.filterwarnings("ignore::pytest.PytestUnhandledThreadExceptionWarning")
    async def test_records_are_delivered_after_the_logging_thread_ended(
        self,
        sdk_logs: pytest.LogCaptureFixture,
        exiting_handler: ExitOnce,
        small_track: getstream_rtc.LocalAudioTrack,
        overflowing_chunk: np.ndarray,
    ) -> None:
        with contextlib.suppress(getstream_rtc.PcmQueueOverflowError):
            await small_track.write_pcm(overflowing_chunk, SAMPLE_RATE, 1)
        assert exiting_handler.raised.wait(timeout=5)
        for thread in threading.enumerate():
            if thread.name == "getstream-logging":
                thread.join(timeout=5)
        getstream_rtc.configure_logging(logging.getLogger("getstream"), logging.DEBUG)

        with contextlib.suppress(getstream_rtc.PcmQueueOverflowError):
            await small_track.write_pcm(overflowing_chunk, SAMPLE_RATE, 1)
        getstream_rtc.logging._flush()

        assert "stream.rtc.audio.pcm_queue_overflow" in sdk_logs.messages

    async def test_a_failed_configure_logging_keeps_the_earlier_logger(
        self,
        sdk_logs: pytest.LogCaptureFixture,
        small_track: getstream_rtc.LocalAudioTrack,
        overflowing_chunk: np.ndarray,
    ) -> None:
        with pytest.raises(TypeError):
            getstream_rtc.configure_logging(
                logging.getLogger("other"), logging.INFO, "WARNING"
            )

        with contextlib.suppress(getstream_rtc.PcmQueueOverflowError):
            await small_track.write_pcm(overflowing_chunk, SAMPLE_RATE, 1)
        getstream_rtc.logging._flush()

        assert any(r.name == "getstream.rtc.tracks.local" for r in sdk_logs.records)

    @pytest.mark.integration
    async def test_log_bodies_logs_request_bodies(
        self, sdk_logs: pytest.LogCaptureFixture, call_users: list[FullUserResponse]
    ) -> None:
        client = getstream_rtc.Client(
            os.environ["STREAM_API_KEY"],
            os.environ["STREAM_API_SECRET"],
            log_bodies=True,
        )
        call = client.call("default", str(uuid.uuid4()))
        await call.join(call_users[0].id)
        await call.leave()
        getstream_rtc.logging._flush()

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
    ) -> None:
        call = rust_client.call("default", str(uuid.uuid4()))
        await call.join(call_users[0].id)
        await call.leave()
        getstream_rtc.logging._flush()

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
    ) -> None:
        logger = logging.getLogger("getstream")
        getstream_rtc.configure_logging(logger, logging.DEBUG, logging.DEBUG)
        call = rust_client.call("default", str(uuid.uuid4()))
        await call.join(call_users[0].id)
        await call.leave()
        getstream_rtc.logging._flush()

        assert [
            r
            for r in sdk_logs.records
            if hasattr(r, "rust_target")
            and not r.rust_target.startswith("getstream::")
            and r.levelno == logging.DEBUG
        ]
