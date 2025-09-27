from __future__ import annotations

import json
import os
import time
from contextlib import contextmanager
from typing import Any, Dict, Optional, Callable, Awaitable
import inspect

# Optional OpenTelemetry imports with graceful fallback
try:
    from opentelemetry import baggage, context as otel_context, metrics, trace
    from opentelemetry.trace import SpanKind, Status, StatusCode

    _HAS_OTEL = True
except Exception:  # pragma: no cover - fallback when OTel not installed
    baggage = None  # type: ignore
    otel_context = None  # type: ignore
    metrics = None  # type: ignore
    trace = None  # type: ignore
    SpanKind = object  # type: ignore
    Status = object  # type: ignore
    StatusCode = object  # type: ignore
    _HAS_OTEL = False


# Env-driven config
INCLUDE_BODIES = os.getenv("STREAM_OTEL_INCLUDE_BODIES", "false").lower() in {
    "1",
    "true",
    "yes",
}
MAX_BODY_CHARS = int(os.getenv("STREAM_OTEL_MAX_BODY_CHARS", "2048"))
REDACT_KEYS = {
    k.strip().lower()
    for k in os.getenv(
        "STREAM_OTEL_REDACT_KEYS",
        "authorization,password,token,secret,api_key,authorization_bearer,auth",
    ).split(",")
}
REDACT_API_KEY = os.getenv("STREAM_OTEL_REDACT_API_KEY", "true").lower() in {
    "1",
    "true",
    "yes",
}


def _noop_cm():  # pragma: no cover - used when OTel missing
    @contextmanager
    def _inner(*_args, **_kwargs):
        yield None

    return _inner()


if _HAS_OTEL:
    _TRACER = trace.get_tracer("getstream")
    _METER = metrics.get_meter("getstream")

    REQ_HIST = _METER.create_histogram(
        name="getstream.client.request.duration",
        unit="ms",
        description="SDK client request latency",
    )
    REQ_COUNT = _METER.create_counter(
        name="getstream.client.request.count",
        description="SDK client requests",
    )
else:  # pragma: no cover - no-op instruments
    _TRACER = None
    REQ_HIST = None
    REQ_COUNT = None


def safe_dump(payload: Any, max_chars: int | None = None) -> str:
    if max_chars is None:
        max_chars = MAX_BODY_CHARS

    def _redact(obj: Any) -> Any:
        if isinstance(obj, dict):
            return {
                k: ("***" if k.lower() in REDACT_KEYS else _redact(v))
                for k, v in obj.items()
            }
        if isinstance(obj, list):
            return [_redact(v) for v in obj]
        return obj

    try:
        s = json.dumps(_redact(payload), ensure_ascii=False)
    except Exception:
        s = str(payload)
    return s[:max_chars]


def common_attributes(
    *,
    api_key: Optional[str],
    endpoint: str,
    method: str,
    url: Optional[str] = None,
    status_code: Optional[int] = None,
) -> Dict[str, Any]:
    attrs: Dict[str, Any] = {
        "stream.endpoint": endpoint,
        "http.request.method": method,
    }
    if url:
        attrs["url.full"] = url
    if status_code is not None:
        attrs["http.response.status_code"] = int(status_code)
    if api_key:
        attrs["stream.api_key"] = api_key
    if _HAS_OTEL and baggage is not None:
        call_cid = baggage.get_baggage("stream.call_cid")
        if call_cid:
            attrs["stream.call_cid"] = call_cid
        channel_cid = baggage.get_baggage("stream.channel_cid")
        if channel_cid:
            attrs["stream.channel_cid"] = channel_cid
    return attrs


def metric_attributes(
    *,
    api_key: Optional[str],
    endpoint: str,
    method: str,
    status_code: Optional[int] = None,
) -> Dict[str, Any]:
    """Build low-cardinality metric attributes.

    - Excludes url.full
    - Excludes stream.call_cid and stream.channel_cid
    - Keeps redacted stream.api_key, endpoint, method, status_code
    """
    attrs: Dict[str, Any] = {
        "stream.endpoint": endpoint,
        "http.request.method": method,
    }
    if status_code is not None:
        attrs["http.response.status_code"] = int(status_code)
    if api_key:
        attrs["stream.api_key"] = api_key
    return attrs


def record_metrics(duration_ms: float, *, attributes: Dict[str, Any]) -> None:
    if not _HAS_OTEL or REQ_HIST is None or REQ_COUNT is None:
        return
    REQ_HIST.record(duration_ms, attributes=attributes)
    REQ_COUNT.add(1, attributes=attributes)


@contextmanager
def span_request(
    name: str,
    *,
    attributes: Optional[Dict[str, Any]] = None,
    include_bodies: Optional[bool] = None,
    request_body: Any = None,
):
    """Start a CLIENT span if OTel is available; otherwise no-op.

    Records exceptions and sets status=ERROR. Adds request body as an event
    when enabled. Records duration on the span as attribute for debugging.
    """
    include_bodies = INCLUDE_BODIES if include_bodies is None else include_bodies
    if not _HAS_OTEL or _TRACER is None:  # pragma: no cover
        start = time.perf_counter()
        try:
            yield None
        finally:
            _ = time.perf_counter() - start
        return

    start = time.perf_counter()
    with _TRACER.start_as_current_span(name, kind=SpanKind.CLIENT) as span:  # type: ignore[arg-type]
        if attributes:
            try:
                span.set_attributes(attributes)  # type: ignore[attr-defined]
            except Exception:
                pass
        if include_bodies and request_body is not None:
            try:
                span.add_event(
                    "request.body", {"level": "INFO", "body": safe_dump(request_body)}
                )  # type: ignore[attr-defined]
            except Exception:
                pass
        try:
            yield span
        except BaseException as e:
            try:
                span.record_exception(e)  # type: ignore[attr-defined]
                span.set_status(Status(StatusCode.ERROR, str(e)))  # type: ignore[attr-defined]
            except Exception:
                pass
            raise
        finally:
            duration_ms = (time.perf_counter() - start) * 1000.0
            try:
                span.set_attribute("getstream.request.duration_ms", duration_ms)  # type: ignore[attr-defined]
            except Exception:
                pass


@contextmanager
def with_call_context(call_cid: str):
    """Attach `stream.call_cid` baggage for the scope of the context (no-op if OTel missing)."""
    if not _HAS_OTEL or baggage is None or otel_context is None:  # pragma: no cover
        yield
        return
    ctx = baggage.set_baggage(
        "stream.call_cid", call_cid, context=otel_context.get_current()
    )
    token = otel_context.attach(ctx)
    try:
        yield
    finally:
        otel_context.detach(token)


def current_operation(default: Optional[str] = None) -> Optional[str]:
    """Return current logical operation name from baggage (stream.operation)."""
    if not _HAS_OTEL or baggage is None:
        return default
    op = baggage.get_baggage("stream.operation")
    return op or default


# Decorators for auto-attaching baggage around method calls
def attach_call_cid(func: Callable[..., Any]) -> Callable[..., Any]:
    def wrapper(self, *args, **kwargs):
        cid = None
        try:
            cid = f"{getattr(self, 'call_type', None)}:{getattr(self, 'id', None)}"
        except Exception:
            cid = None
        op = f"call.{getattr(func, '__name__', 'unknown')}"
        if cid and _HAS_OTEL and baggage is not None and otel_context is not None:
            ctx = baggage.set_baggage(
                "stream.call_cid", cid, context=otel_context.get_current()
            )
            ctx = baggage.set_baggage("stream.operation", op, context=ctx)
            token = otel_context.attach(ctx)
            try:
                return func(self, *args, **kwargs)
            finally:
                otel_context.detach(token)
        return func(self, *args, **kwargs)

    return wrapper


def attach_call_cid_async(
    func: Callable[..., Awaitable[Any]],
) -> Callable[..., Awaitable[Any]]:
    async def wrapper(self, *args, **kwargs):
        cid = None
        try:
            cid = f"{getattr(self, 'call_type', None)}:{getattr(self, 'id', None)}"
        except Exception:
            cid = None
        op = f"call.{getattr(func, '__name__', 'unknown')}"
        if cid and _HAS_OTEL and baggage is not None and otel_context is not None:
            ctx = baggage.set_baggage(
                "stream.call_cid", cid, context=otel_context.get_current()
            )
            ctx = baggage.set_baggage("stream.operation", op, context=ctx)
            token = otel_context.attach(ctx)
            try:
                return await func(self, *args, **kwargs)
            finally:
                otel_context.detach(token)
        return await func(self, *args, **kwargs)

    return wrapper


def attach_channel_cid(func: Callable[..., Any]) -> Callable[..., Any]:
    def wrapper(self, *args, **kwargs):
        cid = None
        try:
            cid = f"{getattr(self, 'channel_type', None)}:{getattr(self, 'channel_id', None)}"
        except Exception:
            cid = None
        op = f"channel.{getattr(func, '__name__', 'unknown')}"
        if cid and _HAS_OTEL and baggage is not None and otel_context is not None:
            # Attach channel_cid to baggage under a different key than call_cid
            ctx = baggage.set_baggage(
                "stream.channel_cid", cid, context=otel_context.get_current()
            )
            ctx = baggage.set_baggage("stream.operation", op, context=ctx)
            token = otel_context.attach(ctx)
            try:
                return func(self, *args, **kwargs)
            finally:
                otel_context.detach(token)
        return func(self, *args, **kwargs)

    return wrapper


def attach_channel_cid_async(
    func: Callable[..., Awaitable[Any]],
) -> Callable[..., Awaitable[Any]]:
    async def wrapper(self, *args, **kwargs):
        cid = None
        try:
            cid = f"{getattr(self, 'channel_type', None)}:{getattr(self, 'channel_id', None)}"
        except Exception:
            cid = None
        op = f"channel.{getattr(func, '__name__', 'unknown')}"
        if cid and _HAS_OTEL and baggage is not None and otel_context is not None:
            ctx = baggage.set_baggage(
                "stream.channel_cid", cid, context=otel_context.get_current()
            )
            ctx = baggage.set_baggage("stream.operation", op, context=ctx)
            token = otel_context.attach(ctx)
            try:
                return await func(self, *args, **kwargs)
            finally:
                otel_context.detach(token)
        return await func(self, *args, **kwargs)

    return wrapper


def operation_name(
    operation: str,
) -> Callable[[Callable[..., Any]], Callable[..., Any]]:
    """Decorator to attach a logical operation name for the wrapped call.

    Usage:
        from getstream.common import telemetry

        @telemetry.operation_name("create_user")
        def create_user(...):
            return self.post(...)
    """

    def decorator(func: Callable[..., Any]) -> Callable[..., Any]:
        if inspect.iscoroutinefunction(func):

            async def async_wrapper(*args, **kwargs):
                if not _HAS_OTEL or baggage is None or otel_context is None:
                    return await func(*args, **kwargs)
                ctx = baggage.set_baggage(
                    "stream.operation", operation, context=otel_context.get_current()
                )
                token = otel_context.attach(ctx)
                try:
                    return await func(*args, **kwargs)
                finally:
                    otel_context.detach(token)

            return async_wrapper

        def wrapper(*args, **kwargs):
            if not _HAS_OTEL or baggage is None or otel_context is None:
                return func(*args, **kwargs)
            ctx = baggage.set_baggage(
                "stream.operation", operation, context=otel_context.get_current()
            )
            token = otel_context.attach(ctx)
            try:
                return func(*args, **kwargs)
            finally:
                otel_context.detach(token)

        return wrapper

    return decorator
