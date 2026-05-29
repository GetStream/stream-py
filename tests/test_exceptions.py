"""Unit tests for the new error hierarchy (CHA-2958).

Covers:
* The four canonical exception classes and their fields.
* APIError envelope parsing into ``StreamApiException`` (incl. spec §6.3
  unparseable-envelope fallback).
* ``Retry-After`` parsing (integer + HTTP-date forms; missing/garbage).
* Transport-error wrapping with ``__cause__`` preserved.
* ``wait_for_task`` sync + async (completed / failed / timeout).
* Back-compat: ``getstream.base.StreamAPIException`` still importable, still
  catchable, emits ``DeprecationWarning``.
"""

from __future__ import annotations

import json
import socket
import ssl
import warnings
from datetime import datetime, timedelta, timezone
from typing import Optional

import httpx
import pytest

from getstream.exceptions import (
    StreamApiException,
    StreamException,
    StreamRateLimitException,
    StreamTaskException,
    StreamTransportException,
    TRANSPORT_ERROR_CONNECTION_RESET,
    TRANSPORT_ERROR_DNS_FAILURE,
    TRANSPORT_ERROR_TIMEOUT,
    TRANSPORT_ERROR_TLS_HANDSHAKE_FAILED,
    TRANSPORT_ERROR_UNKNOWN,
    build_api_exception,
    classify_transport_error,
    parse_retry_after,
    wrap_transport_error,
)


# ── Fixtures ──────────────────────────────────────────────────────────


def _make_response(
    status_code: int,
    body: Optional[dict] = None,
    headers: Optional[dict] = None,
    raw_text: Optional[str] = None,
) -> httpx.Response:
    """Build an ``httpx.Response`` with no real network round-trip."""
    if raw_text is not None:
        content: bytes = raw_text.encode("utf-8")
    elif body is not None:
        content = json.dumps(body).encode("utf-8")
    else:
        content = b""
    request = httpx.Request("GET", "https://example.invalid/test")
    return httpx.Response(
        status_code=status_code,
        content=content,
        headers=headers or {},
        request=request,
    )


# ── Class hierarchy ───────────────────────────────────────────────────


def test_class_hierarchy_matches_spec_9_2():
    """The four concrete classes plus the abstract base all inherit from
    ``StreamException`` per §9.2."""
    assert issubclass(StreamApiException, StreamException)
    assert issubclass(StreamRateLimitException, StreamApiException)
    assert issubclass(StreamTransportException, StreamException)
    assert issubclass(StreamTaskException, StreamException)


def test_api_exception_explicit_kwargs():
    exc = StreamApiException(
        status_code=404,
        code=16,
        message="not found",
        exception_fields={"id": "missing"},
        unrecoverable=True,
        raw_response_body='{"code":16}',
        more_info="https://example.com/docs",
        details=["x"],
    )
    assert exc.status_code == 404
    assert exc.code == 16
    assert exc.message == "not found"
    assert exc.exception_fields == {"id": "missing"}
    assert exc.unrecoverable is True
    assert exc.raw_response_body == '{"code":16}'
    assert exc.more_info == "https://example.com/docs"
    assert exc.details == ["x"]


def test_api_exception_requires_status_code_without_response():
    with pytest.raises(TypeError):
        StreamApiException()


# ── APIError envelope parsing ─────────────────────────────────────────


def test_api_exception_from_response_extracts_all_fields():
    body = {
        "StatusCode": 422,
        "code": 4,
        "duration": "12ms",
        "message": "validation failed",
        "more_info": "https://docs/422",
        "details": [1, 2, 3],
        "exception_fields": {"name": "required"},
        "unrecoverable": False,
    }
    response = _make_response(422, body=body)
    exc = build_api_exception(response)
    assert isinstance(exc, StreamApiException)
    assert not isinstance(exc, StreamRateLimitException)
    assert exc.status_code == 422
    assert exc.code == 4
    assert exc.message == "validation failed"
    assert exc.exception_fields == {"name": "required"}
    assert exc.unrecoverable is False
    assert exc.more_info == "https://docs/422"
    assert exc.details == [1, 2, 3]
    assert exc.raw_response_body == json.dumps(body)


def test_api_exception_exposes_unrecoverable_when_set_true():
    body = {
        "StatusCode": 400,
        "code": 99,
        "duration": "0ms",
        "message": "do not retry",
        "more_info": "",
        "details": [],
        "exception_fields": None,
        "unrecoverable": True,
    }
    exc = build_api_exception(_make_response(400, body=body))
    assert exc.unrecoverable is True


def test_api_exception_unparseable_body_falls_back_per_spec_6_3():
    response = _make_response(500, raw_text="<html>upstream barfed</html>")
    exc = build_api_exception(response)
    assert exc.status_code == 500
    assert exc.code == 0
    assert exc.message == "failed to parse error response"
    assert exc.exception_fields == {}
    assert exc.unrecoverable is False
    assert exc.raw_response_body == "<html>upstream barfed</html>"
    assert exc.api_error is None


def test_api_exception_back_compat_attrs_preserved():
    """The old API surface (api_error, http_response, rate_limit_info,
    status_code) keeps working — none of the existing tests can break."""
    body = {
        "StatusCode": 401,
        "code": 17,
        "duration": "0ms",
        "message": "denied",
        "more_info": "",
        "details": [],
        "exception_fields": None,
    }
    response = _make_response(401, body=body, headers={"x-ratelimit-limit": "10"})
    exc = build_api_exception(response)
    assert exc.http_response is response
    assert exc.status_code == 401
    assert exc.api_error is not None
    assert exc.api_error.code == 17
    # rate_limit_info requires all three headers; only partial here → None.
    assert exc.rate_limit_info is None


# ── Retry-After handling (§7) ─────────────────────────────────────────


def test_parse_retry_after_integer_seconds():
    assert parse_retry_after("30") == timedelta(seconds=30)


def test_parse_retry_after_http_date():
    fake_now = datetime(2026, 1, 1, 12, 0, 0, tzinfo=timezone.utc)
    delta = parse_retry_after(
        "Thu, 01 Jan 2026 12:00:30 GMT",
        now=lambda: fake_now,
    )
    assert delta == timedelta(seconds=30)


def test_parse_retry_after_past_http_date_clamped_to_zero():
    fake_now = datetime(2026, 1, 1, 12, 0, 0, tzinfo=timezone.utc)
    delta = parse_retry_after(
        "Thu, 01 Jan 2026 11:59:30 GMT",
        now=lambda: fake_now,
    )
    assert delta == timedelta(0)


def test_parse_retry_after_missing_or_unparseable_returns_none():
    assert parse_retry_after(None) is None
    assert parse_retry_after("") is None
    assert parse_retry_after("   ") is None
    assert parse_retry_after("not a date or number") is None


def test_parse_retry_after_negative_integer_returns_none():
    assert parse_retry_after("-1") is None


def test_429_builds_rate_limit_exception_with_retry_after():
    body = {
        "StatusCode": 429,
        "code": 9,
        "duration": "0ms",
        "message": "slow down",
        "more_info": "",
        "details": [],
        "exception_fields": None,
    }
    response = _make_response(429, body=body, headers={"Retry-After": "5"})
    exc = build_api_exception(response)
    assert isinstance(exc, StreamRateLimitException)
    # Subclass of StreamApiException — existing 4xx handlers still catch it.
    assert isinstance(exc, StreamApiException)
    assert exc.retry_after == timedelta(seconds=5)
    assert exc.status_code == 429
    assert exc.message == "slow down"


def test_429_without_retry_after_header_is_none():
    body = {
        "StatusCode": 429,
        "code": 9,
        "duration": "0ms",
        "message": "slow down",
        "more_info": "",
        "details": [],
        "exception_fields": None,
    }
    response = _make_response(429, body=body)
    exc = build_api_exception(response)
    assert isinstance(exc, StreamRateLimitException)
    assert exc.retry_after is None


def test_retry_after_exposed_only_on_rate_limit_subclass():
    body = {
        "StatusCode": 500,
        "code": 1,
        "duration": "0ms",
        "message": "boom",
        "more_info": "",
        "details": [],
        "exception_fields": None,
    }
    response = _make_response(500, body=body, headers={"Retry-After": "5"})
    exc = build_api_exception(response)
    assert isinstance(exc, StreamApiException)
    assert not isinstance(exc, StreamRateLimitException)
    assert not hasattr(exc, "retry_after")


# ── Transport-error wrapping (§6.1, §6.4) ─────────────────────────────


def _request() -> httpx.Request:
    return httpx.Request("GET", "https://example.invalid/test")


def test_classify_timeout():
    err = httpx.ReadTimeout("timed out", request=_request())
    assert classify_transport_error(err) == TRANSPORT_ERROR_TIMEOUT


def test_classify_tls_via_cause_chain():
    inner = ssl.SSLError("handshake failed")
    outer = httpx.ConnectError("ssl wrapper", request=_request())
    outer.__cause__ = inner
    assert classify_transport_error(outer) == TRANSPORT_ERROR_TLS_HANDSHAKE_FAILED


def test_classify_dns_via_cause_chain():
    inner = socket.gaierror("name or service not known")
    outer = httpx.ConnectError("dns wrapper", request=_request())
    outer.__cause__ = inner
    assert classify_transport_error(outer) == TRANSPORT_ERROR_DNS_FAILURE


def test_classify_connection_reset_default():
    outer = httpx.ConnectError("connection refused", request=_request())
    assert classify_transport_error(outer) == TRANSPORT_ERROR_CONNECTION_RESET


def test_classify_unknown_for_non_transport_error():
    class WeirdError(Exception):
        pass

    assert classify_transport_error(WeirdError("?")) == TRANSPORT_ERROR_UNKNOWN


def test_wrap_transport_error_builds_exception_class():
    err = httpx.ConnectTimeout("timed out", request=_request())
    wrapped = wrap_transport_error(err)
    assert isinstance(wrapped, StreamTransportException)
    assert wrapped.error_type == TRANSPORT_ERROR_TIMEOUT


def test_transport_exception_cause_chain_preserved():
    """``raise StreamTransportException(...) from err`` must keep the
    underlying httpx error on ``__cause__`` per spec §6.4."""
    err = httpx.ConnectError("refused", request=_request())
    try:
        raise wrap_transport_error(err) from err
    except StreamTransportException as caught:
        assert caught.__cause__ is err
        assert caught.error_type == TRANSPORT_ERROR_CONNECTION_RESET


def _closed_port() -> int:
    """Bind a loopback socket, close it, and return the now-closed port.
    Connecting to it triggers a real ``httpx.ConnectError``."""
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.bind(("127.0.0.1", 0))
    port = s.getsockname()[1]
    s.close()
    return port


def test_transport_wrapping_sync_connection_refused(monkeypatch):
    """End-to-end: a real ``httpx.ConnectError`` (loopback port closed) is
    re-raised by the SDK as ``StreamTransportException`` with the original
    on ``__cause__``."""
    from getstream import Stream

    monkeypatch.delenv("STREAM_API_KEY", raising=False)
    monkeypatch.delenv("STREAM_API_SECRET", raising=False)
    client = Stream(
        api_key="k",
        api_secret="s",
        base_url=f"http://127.0.0.1:{_closed_port()}/",
    )
    try:
        with pytest.raises(StreamTransportException) as info:
            client.get_app()
        assert info.value.error_type in {
            TRANSPORT_ERROR_CONNECTION_RESET,
            TRANSPORT_ERROR_UNKNOWN,
        }
        assert isinstance(info.value.__cause__, httpx.ConnectError)
    finally:
        client.close()


async def test_transport_wrapping_async_read_timeout(httpserver, monkeypatch):
    """A real local server that delays the response longer than the client
    read-timeout triggers ``httpx.ReadTimeout``, wrapped by the SDK as
    ``StreamTransportException`` with ``error_type='timeout'``."""
    import time

    from getstream import AsyncStream

    from werkzeug.wrappers import Response as WerkzeugResponse

    def slow_handler(_request):
        time.sleep(1.0)  # exceed the client's read timeout below
        return WerkzeugResponse("{}", status=200, content_type="application/json")

    httpserver.expect_request("/api/v2/app").respond_with_handler(slow_handler)

    monkeypatch.delenv("STREAM_API_KEY", raising=False)
    monkeypatch.delenv("STREAM_API_SECRET", raising=False)
    client = AsyncStream(
        api_key="k",
        api_secret="s",
        base_url=httpserver.url_for("/"),
        request_timeout=0.2,
    )
    try:
        with pytest.raises(StreamTransportException) as info:
            await client.get_app()
        assert info.value.error_type == TRANSPORT_ERROR_TIMEOUT
        assert isinstance(
            info.value.__cause__, (httpx.ReadTimeout, httpx.TimeoutException)
        )
    finally:
        await client.aclose()


# ── Back-compat alias ─────────────────────────────────────────────────


def test_legacy_alias_still_importable_with_deprecation_warning():
    """``from getstream.base import StreamAPIException`` keeps working but
    emits ``DeprecationWarning`` per spec §10."""
    import getstream.base as base_mod

    with warnings.catch_warnings(record=True) as caught:
        warnings.simplefilter("always")
        legacy = getattr(base_mod, "StreamAPIException")
        assert legacy is StreamApiException
        assert any(
            issubclass(w.category, DeprecationWarning)
            and "StreamAPIException is deprecated" in str(w.message)
            for w in caught
        )


def test_legacy_alias_catches_new_exception():
    """Code that does ``except StreamAPIException`` keeps catching exceptions
    raised by the new code path."""
    from getstream.base import StreamAPIException

    raised = StreamApiException(status_code=500, message="boom")
    with pytest.raises(StreamAPIException) as info:
        raise raised
    assert info.value is raised


# ── wait_for_task (§8) ────────────────────────────────────────────────


_FIXED_NS = int(datetime(2026, 1, 1, 0, 0, 0, tzinfo=timezone.utc).timestamp() * 1e9)


def _task_response(status: str, error: Optional[dict] = None) -> dict:
    """Build a get-task response body matching the real API shape.
    `created_at` / `updated_at` are nanosecond Unix timestamps per the
    backend's wire format."""
    body: dict = {
        "duration": "1ms",
        "task_id": "t",
        "status": status,
        "created_at": _FIXED_NS,
        "updated_at": _FIXED_NS,
    }
    if error is not None:
        body["error"] = error
    return body


def _client_against(httpserver, monkeypatch):
    """Real ``Stream`` instance pointing at the loopback ``httpserver``."""
    from getstream import Stream

    monkeypatch.delenv("STREAM_API_KEY", raising=False)
    monkeypatch.delenv("STREAM_API_SECRET", raising=False)
    return Stream(
        api_key="k",
        api_secret="s",
        base_url=httpserver.url_for("/"),
    )


def _async_client_against(httpserver, monkeypatch):
    from getstream import AsyncStream

    monkeypatch.delenv("STREAM_API_KEY", raising=False)
    monkeypatch.delenv("STREAM_API_SECRET", raising=False)
    return AsyncStream(
        api_key="k",
        api_secret="s",
        base_url=httpserver.url_for("/"),
    )


def test_wait_for_task_sync_returns_on_completed(httpserver, monkeypatch):
    """The helper exits the polling loop the first time the server reports
    ``status='completed'``."""
    bodies = iter(
        [
            _task_response("waiting"),
            _task_response("completed"),
        ]
    )
    from werkzeug.wrappers import Response as WerkzeugResponse

    def handler(_r):
        return WerkzeugResponse(
            json.dumps(next(bodies)),
            status=200,
            content_type="application/json",
        )

    httpserver.expect_request("/api/v2/tasks/task-1").respond_with_handler(handler)

    client = _client_against(httpserver, monkeypatch)
    try:
        result = client.wait_for_task("task-1", poll_interval=0.0, timeout=5.0)
    finally:
        client.close()
    assert result.data.status == "completed"


def test_wait_for_task_sync_raises_on_failed(httpserver, monkeypatch):
    """A ``status='failed'`` response surfaces as ``StreamTaskException``
    populated from the task's ``ErrorResult``."""
    httpserver.expect_request("/api/v2/tasks/task-fail").respond_with_json(
        _task_response(
            "failed",
            error={
                "type": "ImportFailed",
                "description": "bad rows",
                "stacktrace": "trace",
                "version": "v1",
            },
        )
    )

    client = _client_against(httpserver, monkeypatch)
    try:
        with pytest.raises(StreamTaskException) as info:
            client.wait_for_task("task-fail", poll_interval=0.0, timeout=5.0)
    finally:
        client.close()
    exc = info.value
    assert exc.task_id == "task-fail"
    assert exc.error_type == "ImportFailed"
    assert exc.description == "bad rows"
    assert exc.stack_trace == "trace"
    assert exc.version == "v1"


def test_wait_for_task_sync_times_out_raises_transport_exception(
    httpserver, monkeypatch
):
    """A perpetually-waiting task causes the helper to raise
    ``StreamTransportException`` with ``error_type='timeout'``."""
    httpserver.expect_request("/api/v2/tasks/task-timeout").respond_with_json(
        _task_response("waiting")
    )

    client = _client_against(httpserver, monkeypatch)
    try:
        with pytest.raises(StreamTransportException) as info:
            client.wait_for_task("task-timeout", poll_interval=0.05, timeout=0.15)
    finally:
        client.close()
    assert info.value.error_type == TRANSPORT_ERROR_TIMEOUT


async def test_wait_for_task_async_returns_on_completed(httpserver, monkeypatch):
    bodies = iter(
        [
            _task_response("waiting"),
            _task_response("completed"),
        ]
    )
    from werkzeug.wrappers import Response as WerkzeugResponse

    def handler(_r):
        return WerkzeugResponse(
            json.dumps(next(bodies)),
            status=200,
            content_type="application/json",
        )

    httpserver.expect_request("/api/v2/tasks/task-1").respond_with_handler(handler)

    client = _async_client_against(httpserver, monkeypatch)
    try:
        result = await client.wait_for_task("task-1", poll_interval=0.0, timeout=5.0)
    finally:
        await client.aclose()
    assert result.data.status == "completed"


async def test_wait_for_task_async_raises_on_failed(httpserver, monkeypatch):
    httpserver.expect_request("/api/v2/tasks/task-fail").respond_with_json(
        _task_response(
            "failed",
            error={
                "type": "ImportFailed",
                "description": "async bad",
                "stacktrace": None,
                "version": None,
            },
        )
    )

    client = _async_client_against(httpserver, monkeypatch)
    try:
        with pytest.raises(StreamTaskException) as info:
            await client.wait_for_task("task-fail", poll_interval=0.0, timeout=5.0)
    finally:
        await client.aclose()
    assert info.value.task_id == "task-fail"
    assert info.value.description == "async bad"


async def test_wait_for_task_async_times_out_raises_transport_exception(
    httpserver, monkeypatch
):
    httpserver.expect_request("/api/v2/tasks/task-timeout").respond_with_json(
        _task_response("waiting")
    )

    client = _async_client_against(httpserver, monkeypatch)
    try:
        with pytest.raises(StreamTransportException) as info:
            await client.wait_for_task("task-timeout", poll_interval=0.05, timeout=0.15)
    finally:
        await client.aclose()
    assert info.value.error_type == TRANSPORT_ERROR_TIMEOUT


# ── StreamTaskException construction ──────────────────────────────────


def test_stream_task_exception_fields():
    exc = StreamTaskException(
        task_id="t-9",
        error_type="ImportFailed",
        description="boom",
        stack_trace="trace",
        version="v3",
    )
    assert exc.task_id == "t-9"
    assert exc.error_type == "ImportFailed"
    assert exc.description == "boom"
    assert exc.stack_trace == "trace"
    assert exc.version == "v3"
    # Optional fields default to None when not supplied.
    bare = StreamTaskException(task_id="t-0", error_type="x", description="y")
    assert bare.stack_trace is None
    assert bare.version is None
