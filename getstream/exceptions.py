"""Server-side SDK error hierarchy (CHA-2958).

Per the Server-Side SDK Error Handling Spec §9.2, this module defines the
canonical Python error hierarchy:

    StreamException                — abstract base
        StreamApiException         — HTTP 4xx/5xx with APIError envelope
            StreamRateLimitException   — HTTP 429, carries ``retry_after``
        StreamTransportException   — network-layer failure (no HTTP response)
        StreamTaskException        — async task observed as ``status='failed'``

Back-compat: ``getstream.base.StreamAPIException`` (capital ``API``) is an
alias for ``StreamApiException`` for one minor cycle; importing the old name
emits ``DeprecationWarning``.
"""

from __future__ import annotations

import email.utils
import json
import socket
import ssl
from datetime import datetime, timedelta, timezone
from typing import Any, Callable, Dict, Optional, Tuple

import httpx

from getstream.models import APIError
from getstream.rate_limit import RateLimitInfo, extract_rate_limit


TRANSPORT_ERROR_CONNECTION_RESET = "connection_reset"
TRANSPORT_ERROR_TIMEOUT = "timeout"
TRANSPORT_ERROR_DNS_FAILURE = "dns_failure"
TRANSPORT_ERROR_TLS_HANDSHAKE_FAILED = "tls_handshake_failed"
TRANSPORT_ERROR_UNKNOWN = "unknown"


class StreamException(Exception):
    """Abstract base for all Stream SDK errors."""


class StreamApiException(StreamException):
    """Raised on any HTTP 4xx/5xx response from the Stream API.

    Also raised when an HTTP response was received but the body could not be
    parsed as an ``APIError`` envelope (spec §6.3): in that case ``code`` is
    ``0``, ``message`` is ``"failed to parse error response"``, and
    ``__cause__`` is set to the underlying ``ValueError``/``AttributeError``
    via ``raise ... from err`` at the call site (and via the ``response=``
    constructor path internally).
    """

    def __init__(
        self,
        response: Optional[httpx.Response] = None,
        *,
        status_code: Optional[int] = None,
        code: int = 0,
        message: str = "",
        exception_fields: Optional[Dict[str, str]] = None,
        unrecoverable: bool = False,
        raw_response_body: str = "",
        more_info: Optional[str] = None,
        details: Any = None,
        api_error: Optional[APIError] = None,
        rate_limit_info: Optional[RateLimitInfo] = None,
    ) -> None:
        body_parse_err: Optional[BaseException] = None
        if response is not None:
            parsed, body_parse_err = _fields_from_response(response)
            status_code = parsed["status_code"]
            code = parsed["code"]
            message = parsed["message"]
            exception_fields = parsed["exception_fields"]
            unrecoverable = parsed["unrecoverable"]
            raw_response_body = parsed["raw_response_body"]
            more_info = parsed["more_info"]
            details = parsed["details"]
            api_error = parsed["api_error"]
            rate_limit_info = parsed["rate_limit_info"]

        if status_code is None:
            raise TypeError(
                "StreamApiException requires either a response or an explicit status_code"
            )

        self.status_code = status_code
        self.code = code
        self.message = message
        self.exception_fields = exception_fields or {}
        self.unrecoverable = unrecoverable
        self.raw_response_body = raw_response_body
        self.more_info = more_info
        self.details = details
        self.api_error = api_error
        self.rate_limit_info = rate_limit_info
        self.http_response = response
        super().__init__(str(self))
        if body_parse_err is not None and self.__cause__ is None:
            self.__cause__ = body_parse_err

    def __str__(self) -> str:
        if self.code or self.message:
            return (
                f"Stream API error (status={self.status_code}, code={self.code}): "
                f"{self.message}"
            )
        return f"Stream API error (status={self.status_code})"


class StreamRateLimitException(StreamApiException):
    """HTTP 429. Carries ``retry_after`` parsed from the ``Retry-After`` header.

    ``retry_after`` is ``None`` when the header is absent or unparseable
    (graceful — never raises on a bad header).
    """

    def __init__(
        self,
        response: Optional[httpx.Response] = None,
        *,
        retry_after: Optional[timedelta] = None,
        **kwargs: Any,
    ) -> None:
        if response is not None and retry_after is None:
            retry_after = parse_retry_after(response.headers.get("Retry-After"))
        super().__init__(response, **kwargs)
        self.retry_after = retry_after


class StreamTransportException(StreamException):
    """Network-layer failure: connection reset, timeout, TLS, DNS, etc.

    No HTTP response was received. Callers MUST set ``__cause__`` via
    ``raise StreamTransportException(...) from err`` so users can recover
    the original transport error.
    """

    def __init__(self, error_type: str, message: str = "") -> None:
        self.error_type = error_type
        super().__init__(message or f"Stream transport error ({error_type})")


class StreamTaskException(StreamException):
    """Raised by ``wait_for_task`` when the polled task ends in
    ``status='failed'``. Fields mirror the ``ErrorResult`` envelope on the
    task-status response.
    """

    def __init__(
        self,
        *,
        task_id: str,
        error_type: str,
        description: str,
        stack_trace: Optional[str] = None,
        version: Optional[str] = None,
    ) -> None:
        self.task_id = task_id
        self.error_type = error_type
        self.description = description
        self.stack_trace = stack_trace
        self.version = version
        super().__init__(f"Task {task_id} failed ({error_type}): {description}")


def _fields_from_response(
    response: httpx.Response,
) -> Tuple[Dict[str, Any], Optional[BaseException]]:
    """Pull the §5.1 fields out of an httpx response.

    Returns ``(fields, parse_error)`` where ``parse_error`` is the
    ``ValueError`` or ``TypeError`` that prevented body decoding, or ``None``
    when the body parsed cleanly as an ``APIError`` envelope (or the body was
    empty).
    """
    raw_body = ""
    try:
        raw_body = response.text or ""
    except Exception:
        pass

    api_error: Optional[APIError] = None
    parse_error: Optional[BaseException] = None
    if response.content:
        try:
            parsed_json: Any = json.loads(response.content)
            api_error = APIError.from_dict(parsed_json)
        except (ValueError, AttributeError, TypeError) as e:
            api_error = None
            parse_error = e

    rate_limit_info = extract_rate_limit(response)

    if api_error is not None:
        unrecoverable = api_error.unrecoverable
        return (
            {
                "status_code": response.status_code,
                "code": api_error.code,
                "message": api_error.message,
                "exception_fields": dict(api_error.exception_fields or {}),
                "unrecoverable": bool(unrecoverable)
                if unrecoverable is not None
                else False,
                "raw_response_body": raw_body,
                "more_info": api_error.more_info or None,
                "details": api_error.details,
                "api_error": api_error,
                "rate_limit_info": rate_limit_info,
            },
            None,
        )

    return (
        {
            "status_code": response.status_code,
            "code": 0,
            "message": "failed to parse error response",
            "exception_fields": {},
            "unrecoverable": False,
            "raw_response_body": raw_body,
            "more_info": None,
            "details": None,
            "api_error": None,
            "rate_limit_info": rate_limit_info,
        },
        parse_error,
    )


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


def parse_retry_after(
    header_value: Optional[str],
    *,
    now: Callable[[], datetime] = _utcnow,
) -> Optional[timedelta]:
    """Parse ``Retry-After`` per RFC 7231 §7.1.3.

    Accepts integer seconds (``Retry-After: 30``) or HTTP-date
    (``Retry-After: Fri, 31 Dec 2026 23:59:59 GMT``). Returns ``None`` when
    the header is absent or unparseable. HTTP-date deltas in the past are
    clamped to zero (never negative).
    """
    if header_value is None:
        return None
    value = header_value.strip()
    if not value:
        return None
    try:
        seconds = int(value)
    except ValueError:
        pass
    else:
        if seconds < 0:
            return None
        return timedelta(seconds=seconds)

    try:
        parsed = email.utils.parsedate_to_datetime(value)
    except (TypeError, ValueError):
        return None
    if parsed is None:
        return None
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=timezone.utc)
    delta = parsed - now()
    if delta.total_seconds() < 0:
        return timedelta(0)
    return delta


def build_api_exception(response: httpx.Response) -> StreamApiException:
    """Build the right ``StreamApiException`` subclass from an httpx response.

    * 429 → ``StreamRateLimitException`` with parsed ``Retry-After``.
    * otherwise → base ``StreamApiException``.

    The ``__cause__`` chain is populated from any body-parse failure
    encountered while extracting the ``APIError`` envelope (spec §6.3).
    """
    if response.status_code == 429:
        return StreamRateLimitException(response=response)
    return StreamApiException(response=response)


def classify_transport_error(exc: BaseException) -> str:
    """Map an httpx transport-layer exception to the spec ``error_type`` enum.

    Walks the ``__cause__``/``__context__`` chain to catch the underlying
    ``ssl.SSLError`` or ``socket.gaierror`` that httpx wraps. Falls back to
    generic ``connection_reset`` for network errors and ``unknown`` for
    anything we don't recognize.
    """
    if isinstance(exc, httpx.TimeoutException):
        return TRANSPORT_ERROR_TIMEOUT

    seen: set = set()
    cur: Optional[BaseException] = exc
    while cur is not None and id(cur) not in seen:
        seen.add(id(cur))
        if isinstance(cur, ssl.SSLError):
            return TRANSPORT_ERROR_TLS_HANDSHAKE_FAILED
        if isinstance(cur, socket.gaierror):
            return TRANSPORT_ERROR_DNS_FAILURE
        cur = cur.__cause__ or cur.__context__

    if isinstance(exc, (httpx.NetworkError, httpx.TransportError)):
        return TRANSPORT_ERROR_CONNECTION_RESET
    return TRANSPORT_ERROR_UNKNOWN


def wrap_transport_error(exc: httpx.RequestError) -> StreamTransportException:
    """Build a ``StreamTransportException`` from an httpx ``RequestError``.

    Caller is expected to ``raise ... from exc`` so ``__cause__`` is set per
    spec §6.4.
    """
    return StreamTransportException(
        error_type=classify_transport_error(exc),
        message=f"transport error: {exc}",
    )


__all__ = [
    "StreamException",
    "StreamApiException",
    "StreamRateLimitException",
    "StreamTransportException",
    "StreamTaskException",
    "TRANSPORT_ERROR_CONNECTION_RESET",
    "TRANSPORT_ERROR_TIMEOUT",
    "TRANSPORT_ERROR_DNS_FAILURE",
    "TRANSPORT_ERROR_TLS_HANDSHAKE_FAILED",
    "TRANSPORT_ERROR_UNKNOWN",
    "build_api_exception",
    "classify_transport_error",
    "parse_retry_after",
    "wrap_transport_error",
]
