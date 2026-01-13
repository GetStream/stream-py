from __future__ import annotations

import json
import os
from contextlib import contextmanager
from typing import Any, Dict, Optional, Callable, Awaitable, TYPE_CHECKING
from contextvars import ContextVar
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
    # Tracer must be retrieved lazily to respect late provider configuration
    def _get_tracer():
        return trace.get_tracer("getstream")

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

    def _get_tracer():  # pragma: no cover - no-op
        return None

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
    client_request_id: Optional[str] = None,
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
    if client_request_id:
        attrs["stream.client_request_id"] = client_request_id
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
    if not _HAS_OTEL:  # pragma: no cover
        yield _NullSpan()
        return
    tracer = _get_tracer()
    if tracer is None:
        yield _NullSpan()  # pragma: no cover
        return
    with tracer.start_as_current_span(name, kind=SpanKind.CLIENT) as span:
        base_attrs: Dict[str, Any] = dict(attributes or {})
        # auto-propagate contextual IDs to request spans
        try:
            cid = get_current_call_cid()
            if cid:
                base_attrs["stream.call_cid"] = cid
            ch = get_current_channel_cid()
            if ch:
                base_attrs["stream.channel_cid"] = ch
        except Exception:
            pass
        if base_attrs:
            try:
                span.set_attributes(base_attrs)
            except Exception:
                pass
        if include_bodies and request_body is not None:
            try:
                span.add_event(
                    "request.body", {"level": "INFO", "body": safe_dump(request_body)}
                )
            except Exception:
                pass
        try:
            yield span
        except BaseException as e:
            try:
                span.record_exception(e)
                span.set_status(Status(StatusCode.ERROR, str(e)))
            except Exception:
                pass
            raise


def current_operation(default: Optional[str] = None) -> Optional[str]:
    """Return default; baggage-based lookup removed."""
    return default


# Lightweight, context-local storage for call/channel CIDs
_CTX_CALL_CID: ContextVar[Optional[str]] = ContextVar("_stream_call_cid", default=None)
_CTX_CHANNEL_CID: ContextVar[Optional[str]] = ContextVar(
    "_stream_channel_cid", default=None
)


def get_current_call_cid() -> Optional[str]:
    return _CTX_CALL_CID.get()


def get_current_channel_cid() -> Optional[str]:
    return _CTX_CHANNEL_CID.get()


# Decorators for auto-attaching contextual IDs around method calls
def attach_call_cid(func: Callable[..., Any]) -> Callable[..., Any]:
    def wrapper(self: BaseCall, *args, **kwargs):
        cid = f"{self.call_type}:{self.id}"
        token = _CTX_CALL_CID.set(cid)
        try:
            return func(self, *args, **kwargs)
        finally:
            _CTX_CALL_CID.reset(token)

    # also expose for introspection if needed
    setattr(wrapper, "_call_cid_attacher", True)
    return wrapper


def attach_call_cid_async(
    func: Callable[..., Awaitable[Any]],
) -> Callable[..., Awaitable[Any]]:
    async def wrapper(self: BaseCall, *args, **kwargs):
        cid = f"{self.call_type}:{self.id}"
        token = _CTX_CALL_CID.set(cid)
        try:
            return await func(self, *args, **kwargs)
        finally:
            _CTX_CALL_CID.reset(token)

    setattr(wrapper, "_call_cid_attacher", True)
    return wrapper


def attach_channel_cid(func: Callable[..., Any]) -> Callable[..., Any]:
    def wrapper(self: Channel, *args, **kwargs):
        cid = f"{self.channel_type}:{self.channel_id}"
        token = _CTX_CHANNEL_CID.set(cid)
        try:
            return func(self, *args, **kwargs)
        finally:
            _CTX_CHANNEL_CID.reset(token)

    setattr(wrapper, "_channel_cid_attacher", True)
    return wrapper


def attach_channel_cid_async(
    func: Callable[..., Awaitable[Any]],
) -> Callable[..., Awaitable[Any]]:
    async def wrapper(self: Channel, *args, **kwargs):
        cid = f"{self.channel_type}:{self.channel_id}"
        token = _CTX_CHANNEL_CID.set(cid)
        try:
            return await func(self, *args, **kwargs)
        finally:
            _CTX_CHANNEL_CID.reset(token)

    setattr(wrapper, "_channel_cid_attacher", True)
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
    if not _HAS_OTEL:  # pragma: no cover
        yield _NullSpan()
        return
    use_kind = kind if kind is not None else SpanKind.INTERNAL
    tracer = _get_tracer()
    if tracer is None:  # pragma: no cover
        yield _NullSpan()
        return
    with tracer.start_as_current_span(name, kind=use_kind) as span:
        base_attrs: Dict[str, Any] = dict(attributes or {})
        # auto-propagate contextual IDs
        try:
            cid = get_current_call_cid()
            if cid:
                base_attrs["stream.call_cid"] = cid
            ch = get_current_channel_cid()
            if ch:
                base_attrs["stream.channel_cid"] = ch
        except Exception:
            pass
        if base_attrs:
            try:
                span.set_attributes(base_attrs)
            except Exception:
                pass
        yield span


def get_current_span():
    if not _HAS_OTEL:  # pragma: no cover
        return _NullSpan()
    return trace.get_current_span()


def set_span_in_context(span: "Span", context: Optional["Context"] = None):
    """Attach the given span into the current context.

    Returns an attach token suitable for later detaching via `detach_context`.
    If OpenTelemetry is unavailable, returns None.
    """
    if not _HAS_OTEL or otel_context is None:  # pragma: no cover
        return None
    ctx = trace.set_span_in_context(span, context or otel_context.get_current())
    token = otel_context.attach(ctx)
    return token


def detach_context(token: Optional[object]) -> None:
    """Detach a previously attached context token (safe no-op)."""
    if not _HAS_OTEL or otel_context is None or token is None:  # pragma: no cover
        return
    try:
        otel_context.detach(token)  # type: ignore[arg-type]
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
