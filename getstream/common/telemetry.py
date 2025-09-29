from __future__ import annotations

import json
import os
import time
from contextlib import contextmanager
from typing import Any, Dict, Optional, Callable, Awaitable, TYPE_CHECKING
import inspect

if TYPE_CHECKING:
    from getstream.chat.channel import Channel
    from getstream.video import BaseCall

# Optional OpenTelemetry imports with graceful fallback
try:
    from opentelemetry import context as otel_context, metrics, trace
    from opentelemetry.trace import SpanKind, Status, StatusCode
    from opentelemetry.trace.span import Span
    from opentelemetry.context.context import Context

    _HAS_OTEL = True
except Exception:  # pragma: no cover - fallback when OTel not installed
    otel_context = None  # type: ignore
    metrics = None  # type: ignore
    trace = None  # type: ignore
    SpanKind = object  # type: ignore
    Span = object  # type: ignore
    Status = object  # type: ignore
    StatusCode = object  # type: ignore
    Context = object  # type: ignore
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
    return attrs


def metric_attributes(
    *,
    api_key: Optional[str],
    endpoint: str,
    method: str,
    status_code: Optional[int] = None,
) -> Dict[str, Any]:
    """Build low-cardinality metric attributes.

    - Excludes url.full and high-cardinality IDs
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


def current_operation(default: Optional[str] = None) -> Optional[str]:
    """Return default; baggage-based lookup removed."""
    return default


# Decorators for auto-attaching baggage around method calls
def attach_call_cid(func: Callable[..., Any]) -> Callable[..., Any]:
    def wrapper(self: BaseCall, *args, **kwargs):
        cid = f"{self.call_type}:{self.id}"
        client = getattr(self, "client", None)
        prev = getattr(client, "_call_cid", None) if client is not None else None
        if client is not None:
            setattr(client, "_call_cid", cid)
        try:
            return func(self, *args, **kwargs)
        finally:
            if client is not None:
                if prev is not None:
                    setattr(client, "_call_cid", prev)
                else:
                    try:
                        delattr(client, "_call_cid")
                    except Exception:
                        pass

    return wrapper


def attach_call_cid_async(
    func: Callable[..., Awaitable[Any]],
) -> Callable[..., Awaitable[Any]]:
    async def wrapper(self: BaseCall, *args, **kwargs):
        cid = f"{self.call_type}:{self.id}"
        client = getattr(self, "client", None)
        prev = getattr(client, "_call_cid", None) if client is not None else None
        if client is not None:
            setattr(client, "_call_cid", cid)
        try:
            return await func(self, *args, **kwargs)
        finally:
            if client is not None:
                if prev is not None:
                    setattr(client, "_call_cid", prev)
                else:
                    try:
                        delattr(client, "_call_cid")
                    except Exception:
                        pass

    return wrapper


def attach_channel_cid(func: Callable[..., Any]) -> Callable[..., Any]:
    def wrapper(self: Channel, *args, **kwargs):
        cid = f"{self.channel_type}:{self.channel_id}"
        client = getattr(self, "client", None)
        prev = getattr(client, "_channel_cid", None) if client is not None else None
        if client is not None:
            setattr(client, "_channel_cid", cid)
        try:
            return func(self, *args, **kwargs)
        finally:
            if client is not None:
                if prev is not None:
                    setattr(client, "_channel_cid", prev)
                else:
                    try:
                        delattr(client, "_channel_cid")
                    except Exception:
                        pass

    return wrapper


def attach_channel_cid_async(
    func: Callable[..., Awaitable[Any]],
) -> Callable[..., Awaitable[Any]]:
    async def wrapper(self: Channel, *args, **kwargs):
        cid = f"{self.channel_type}:{self.channel_id}"
        client = getattr(self, "client", None)
        prev = getattr(client, "_channel_cid", None) if client is not None else None
        if client is not None:
            setattr(client, "_channel_cid", cid)
        try:
            return await func(self, *args, **kwargs)
        finally:
            if client is not None:
                if prev is not None:
                    setattr(client, "_channel_cid", prev)
                else:
                    try:
                        delattr(client, "_channel_cid")
                    except Exception:
                        pass

    return wrapper


class _NullSpan:  # pragma: no cover - used when OTel is missing
    def set_attribute(self, *args, **kwargs):
        return None

    def set_attributes(self, *args, **kwargs):
        return None

    def add_event(self, *args, **kwargs):
        return None

    def record_exception(self, *args, **kwargs):
        return None

    def set_status(self, *args, **kwargs):
        return None

    def end(self):
        return None

    def is_recording(self) -> bool:
        return False


@contextmanager
def start_as_current_span(
    name: str,
    *,
    kind: Optional["SpanKind"] = None,
    attributes: Optional[Dict[str, Any]] = None,
):
    """Lightweight span context manager that no-ops if OTel isn't available."""
    if not _HAS_OTEL or _TRACER is None:  # pragma: no cover
        yield _NullSpan()
        return
    use_kind = kind if kind is not None else SpanKind.INTERNAL
    with _TRACER.start_as_current_span(name, kind=use_kind) as span:  # type: ignore[arg-type]
        if attributes:
            try:
                span.set_attributes(attributes)  # type: ignore[attr-defined]
            except Exception:
                pass
        yield span


def get_current_span():
    if not _HAS_OTEL or _TRACER is None:  # pragma: no cover
        return _NullSpan()
    return trace.get_current_span()


def set_span_in_context(span: "Span", context: Optional["Context"] = None):
    """Attach the given span into the current context.

    Returns an attach token suitable for later detaching via `detach_context`.
    If OpenTelemetry is unavailable, returns None.
    """
    if not _HAS_OTEL or _TRACER is None or otel_context is None:  # pragma: no cover
        return None
    ctx = trace.set_span_in_context(span, context or otel_context.get_current())
    token = otel_context.attach(ctx)
    return token


def detach_context(token: Optional[object]) -> None:
    """Detach a previously attached context token (safe no-op)."""
    if not _HAS_OTEL or otel_context is None or token is None:  # pragma: no cover
        return
    try:
        otel_context.detach(token)
    except Exception:
        # Best-effort; do not raise during detach
        pass


@contextmanager
def attach_span(span: "Span"):
    """Context manager to attach a span to the current context for the block."""
    token = set_span_in_context(span)
    try:
        yield
    finally:
        detach_context(token)


def with_span(
    name: str,
    *,
    kind: Optional["SpanKind"] = None,
    attributes: Optional[Dict[str, Any]] = None,
) -> Callable[[Callable[..., Any]], Callable[..., Any]]:
    """Decorator to wrap a function in a span (sync or async)."""

    def decorator(func: Callable[..., Any]) -> Callable[..., Any]:
        if inspect.iscoroutinefunction(func):

            async def async_wrapper(*args, **kwargs):
                with start_as_current_span(name, kind=kind, attributes=attributes):
                    return await func(*args, **kwargs)

            return async_wrapper

        def wrapper(*args, **kwargs):
            with start_as_current_span(name, kind=kind, attributes=attributes):
                return func(*args, **kwargs)

        return wrapper

    return decorator


def add_event(name: str, attributes: Optional[Dict[str, Any]] = None) -> None:
    """Add an event to the current span if recording; otherwise no-op."""
    if not _HAS_OTEL or trace is None:  # pragma: no cover
        return
    try:
        span = trace.get_current_span()
        if span is not None and getattr(span, "is_recording", lambda: False)():
            span.add_event(name, attributes or {})
    except Exception:
        return


def operation_name(operation: str):
    def decorator(func):
        async def async_wrapper(self, *args, **kwargs):
            self._operation_name = operation
            return await func(self, *args, **kwargs)

        def wrapper(self, *args, **kwargs):
            self._operation_name = operation
            return func(self, *args, **kwargs)

        return async_wrapper if inspect.iscoroutinefunction(func) else wrapper

    return decorator
