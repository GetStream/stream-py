from datetime import timedelta

import httpx
import pytest

from getstream import AsyncStream, RetryConfig, Stream
from getstream.base import _retry_delay, _retry_eligible
from getstream.exceptions import (
    StreamRateLimitException,
    StreamTransportException,
)


def rate_limited_body(unrecoverable=False):
    """A fully-populated APIError envelope (all required fields present) so
    the exception layer parses it instead of falling back to the generic
    "failed to parse error response" path."""
    return {
        "code": 9,
        "duration": "0ms",
        "message": "too many requests",
        "more_info": "",
        "StatusCode": 429,
        "details": [],
        "unrecoverable": unrecoverable,
    }


class Counter:
    def __init__(self, responses):
        self.responses = responses
        self.calls = 0

    def __call__(self, request: httpx.Request) -> httpx.Response:
        step = self.responses[self.calls]
        self.calls += 1
        if isinstance(step, Exception):
            raise step
        return step


def sync_client(counter, retry=None, monkeypatch=None):
    if monkeypatch is not None:
        monkeypatch.setattr("time.sleep", lambda _s: None)
    return Stream(
        api_key="key",
        api_secret="secret",
        transport=httpx.MockTransport(counter),
        retry=retry,
    )


def async_client(counter, retry=None, monkeypatch=None):
    if monkeypatch is not None:

        async def no_sleep(_s):
            return None

        monkeypatch.setattr("asyncio.sleep", no_sleep)
    return AsyncStream(
        api_key="key",
        api_secret="secret",
        transport=httpx.MockTransport(counter),
        retry=retry,
    )


ENABLED = RetryConfig(enabled=True, max_attempts=3, max_backoff=0.001)


# ── sync ────────────────────────────────────────────────────────────


def test_disabled_by_default_single_attempt(monkeypatch):
    counter = Counter(
        [httpx.Response(429, headers={"Retry-After": "1"}, json=rate_limited_body())]
    )
    client = sync_client(counter, monkeypatch=monkeypatch)
    with pytest.raises(StreamRateLimitException):
        client.get("/api/v2/app")
    assert counter.calls == 1


def test_enabled_get_retries_429_then_succeeds(monkeypatch, caplog):
    import logging

    logger = logging.getLogger("test.retry.sync")
    caplog.set_level(logging.DEBUG, logger="test.retry.sync")
    counter = Counter(
        [
            httpx.Response(429, json=rate_limited_body()),
            httpx.Response(200, json={}),
        ]
    )
    client = Stream(
        api_key="key",
        api_secret="secret",
        transport=httpx.MockTransport(counter),
        retry=ENABLED,
        logger=logger,
    )
    monkeypatch.setattr("time.sleep", lambda _s: None)
    client.get("/api/v2/app")
    assert counter.calls == 2
    failed = [r for r in caplog.records if r.getMessage() == "http.request.failed"]
    assert len(failed) == 1
    assert failed[0].levelno == logging.DEBUG
    # Cross-SDK rule: a retried 429 must not carry error.type (transport-only enum).
    assert not hasattr(failed[0], "error.type")
    assert getattr(failed[0], "retry.attempt") == 1


def test_enabled_post_never_retried(monkeypatch):
    counter = Counter([httpx.Response(429, json=rate_limited_body())])
    client = sync_client(counter, retry=ENABLED, monkeypatch=monkeypatch)
    with pytest.raises(StreamRateLimitException):
        client.post("/api/v2/x", json={})
    assert counter.calls == 1


def test_unrecoverable_never_retried(monkeypatch):
    counter = Counter([httpx.Response(429, json=rate_limited_body(unrecoverable=True))])
    client = sync_client(counter, retry=ENABLED, monkeypatch=monkeypatch)
    with pytest.raises(StreamRateLimitException):
        client.get("/api/v2/app")
    assert counter.calls == 1


def test_transport_error_retried(monkeypatch, caplog):
    import logging

    logger = logging.getLogger("test.retry.sync.transport")
    caplog.set_level(logging.DEBUG, logger="test.retry.sync.transport")
    counter = Counter(
        [
            httpx.ConnectError("reset"),
            httpx.Response(200, json={}),
        ]
    )
    client = Stream(
        api_key="key",
        api_secret="secret",
        transport=httpx.MockTransport(counter),
        retry=ENABLED,
        logger=logger,
    )
    monkeypatch.setattr("time.sleep", lambda _s: None)
    client.get("/api/v2/app")
    assert counter.calls == 2
    failed = [r for r in caplog.records if r.getMessage() == "http.request.failed"]
    assert len(failed) == 1
    assert failed[0].levelno == logging.DEBUG
    # Transport failures DO carry error.type (the closed transport-only enum).
    assert hasattr(failed[0], "error.type")


def test_exhaustion_surfaces_last_error(monkeypatch):
    counter = Counter([httpx.Response(429, json=rate_limited_body())] * 3)
    client = sync_client(counter, retry=ENABLED, monkeypatch=monkeypatch)
    with pytest.raises(StreamRateLimitException):
        client.get("/api/v2/app")
    assert counter.calls == 3


def test_transport_exhaustion_logs_final_error(monkeypatch, caplog):
    import logging

    logger = logging.getLogger("test.retry.sync.exhaust")
    caplog.set_level(logging.DEBUG, logger="test.retry.sync.exhaust")
    counter = Counter([httpx.ConnectError("reset")] * 3)
    client = Stream(
        api_key="key",
        api_secret="secret",
        transport=httpx.MockTransport(counter),
        retry=ENABLED,
        logger=logger,
    )
    monkeypatch.setattr("time.sleep", lambda _s: None)
    with pytest.raises(StreamTransportException):
        client.get("/api/v2/app")
    assert counter.calls == 3
    failed = [r for r in caplog.records if r.getMessage() == "http.request.failed"]
    # 2 retried attempts at DEBUG, 1 final at ERROR.
    assert len(failed) == 3
    assert [r.levelno for r in failed] == [logging.DEBUG, logging.DEBUG, logging.ERROR]
    assert all(hasattr(r, "error.type") for r in failed)


def test_disabled_transport_failure_logs_identical_to_today(monkeypatch, caplog):
    """With retry disabled (default), logging must be unchanged: exactly one
    ERROR http.request.failed, no DEBUG retry-log noise."""
    import logging

    logger = logging.getLogger("test.retry.sync.disabled")
    caplog.set_level(logging.DEBUG, logger="test.retry.sync.disabled")
    counter = Counter([httpx.ConnectError("reset")])
    client = Stream(
        api_key="key",
        api_secret="secret",
        transport=httpx.MockTransport(counter),
        logger=logger,
    )
    with pytest.raises(StreamTransportException):
        client.get("/api/v2/app")
    failed = [r for r in caplog.records if r.getMessage() == "http.request.failed"]
    assert len(failed) == 1
    assert failed[0].levelno == logging.ERROR


def test_delay_clamp_and_jitter_bounds():
    retry = RetryConfig(enabled=True, max_attempts=3, max_backoff=30.0)
    exc = StreamRateLimitException(status_code=429, retry_after=timedelta(seconds=600))
    assert _retry_delay(retry, exc, 0) == 30.0
    transport = StreamTransportException("timeout")
    for attempt in range(3):
        ceil = min(30.0, 2.0**attempt)
        for _ in range(50):
            assert 0 <= _retry_delay(retry, transport, attempt) <= ceil


def test_eligibility_matrix():
    retry = RetryConfig(enabled=True, max_attempts=3)
    transport = StreamTransportException("timeout")
    assert _retry_eligible(retry, transport, "GET", 0)
    assert _retry_eligible(retry, transport, "HEAD", 1)
    assert not _retry_eligible(retry, transport, "POST", 0)
    assert not _retry_eligible(retry, transport, "GET", 2)
    assert not _retry_eligible(None, transport, "GET", 0)
    assert not _retry_eligible(RetryConfig(), transport, "GET", 0)


def test_unrecoverable_not_eligible():
    retry = RetryConfig(enabled=True, max_attempts=3)
    rate_limited = StreamRateLimitException(status_code=429, unrecoverable=True)
    assert not _retry_eligible(retry, rate_limited, "GET", 0)


def test_retry_config_validation():
    with pytest.raises(ValueError):
        RetryConfig(max_attempts=0)
    with pytest.raises(ValueError):
        RetryConfig(max_backoff=-1.0)


# ── async ───────────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_async_disabled_by_default_single_attempt():
    counter = Counter([httpx.Response(429, json=rate_limited_body())])
    client = async_client(counter)
    with pytest.raises(StreamRateLimitException):
        await client.get("/api/v2/app")
    assert counter.calls == 1
    await client.aclose()


@pytest.mark.asyncio
async def test_async_enabled_get_retries(monkeypatch):
    counter = Counter(
        [
            httpx.Response(429, json=rate_limited_body()),
            httpx.Response(200, json={}),
        ]
    )
    client = async_client(counter, retry=ENABLED, monkeypatch=monkeypatch)
    await client.get("/api/v2/app")
    assert counter.calls == 2
    await client.aclose()


@pytest.mark.asyncio
async def test_async_post_never_retried(monkeypatch):
    counter = Counter([httpx.Response(429, json=rate_limited_body())])
    client = async_client(counter, retry=ENABLED, monkeypatch=monkeypatch)
    with pytest.raises(StreamRateLimitException):
        await client.post("/api/v2/x", json={})
    assert counter.calls == 1
    await client.aclose()


@pytest.mark.asyncio
async def test_async_unrecoverable_never_retried(monkeypatch):
    counter = Counter([httpx.Response(429, json=rate_limited_body(unrecoverable=True))])
    client = async_client(counter, retry=ENABLED, monkeypatch=monkeypatch)
    with pytest.raises(StreamRateLimitException):
        await client.get("/api/v2/app")
    assert counter.calls == 1
    await client.aclose()


@pytest.mark.asyncio
async def test_async_transport_error_retried(monkeypatch):
    counter = Counter(
        [
            httpx.ConnectError("reset"),
            httpx.Response(200, json={}),
        ]
    )
    client = async_client(counter, retry=ENABLED, monkeypatch=monkeypatch)
    await client.get("/api/v2/app")
    assert counter.calls == 2
    await client.aclose()


@pytest.mark.asyncio
async def test_async_exhaustion_surfaces_last_error(monkeypatch):
    counter = Counter([httpx.Response(429, json=rate_limited_body())] * 3)
    client = async_client(counter, retry=ENABLED, monkeypatch=monkeypatch)
    with pytest.raises(StreamRateLimitException):
        await client.get("/api/v2/app")
    assert counter.calls == 3
    await client.aclose()


@pytest.mark.asyncio
async def test_async_retry_after_honored(monkeypatch):
    """retry_after honored on the async path too, and clamped to max_backoff."""
    slept = []

    async def capture_sleep(seconds):
        slept.append(seconds)

    monkeypatch.setattr("asyncio.sleep", capture_sleep)
    counter = Counter(
        [
            httpx.Response(429, headers={"Retry-After": "5"}, json=rate_limited_body()),
            httpx.Response(200, json={}),
        ]
    )
    retry = RetryConfig(enabled=True, max_attempts=3, max_backoff=1.0)
    client = AsyncStream(
        api_key="key",
        api_secret="secret",
        transport=httpx.MockTransport(counter),
        retry=retry,
    )
    await client.get("/api/v2/app")
    assert counter.calls == 2
    assert slept == [1.0]  # clamped from 5s to max_backoff=1.0
    await client.aclose()
