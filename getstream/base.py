import json
import logging
import mimetypes
import os
import random
import time
import uuid
import warnings
import asyncio
from typing import Any, Dict, List, Optional, Tuple, Type, cast, get_origin

from getstream.exceptions import (
    StreamApiException,
    StreamRateLimitException,
    StreamTransportException,
    build_api_exception,
    wrap_transport_error,
)
from getstream.logging_utils import redact_json_body, redact_query
from getstream.stream_response import StreamResponse
from getstream.generic import T
import httpx
from getstream.config import BaseConfig
from getstream.version import VERSION
from urllib.parse import quote
from abc import ABC
from getstream.common.telemetry import (
    common_attributes,
    record_metrics,
    span_request,
    current_operation,
    metric_attributes,
    with_span,
    get_current_call_cid,
    get_current_channel_cid,
)
import ijson


# ── Connection pool defaults (CHA-2956) ──────────────────────────────
# Kept in sync with getstream.stream constants; duplicated here so BaseClient/AsyncBaseClient can be instantiated standalone (e.g. by sub-clients constructed directly without going through Stream/AsyncStream).
DEFAULT_MAX_CONNS_PER_HOST = 5
DEFAULT_IDLE_TIMEOUT = 55.0
DEFAULT_CONNECT_TIMEOUT = 10.0


logger = logging.getLogger("getstream")


# ── Retry policy (CHA-2959) ───────────────────────────────────────────
def _retry_eligible(retry, exc, method: str, attempt: int) -> bool:
    """Whether ``exc`` from the given 0-indexed ``attempt`` should be retried
    under ``retry`` (a ``RetryConfig`` or ``None``). Only GET/HEAD, only HTTP
    429 (unless marked unrecoverable) or a transport error, and only while
    attempts remain."""
    if retry is None or not retry.enabled:
        return False
    if method.upper() not in ("GET", "HEAD"):
        return False
    if attempt + 1 >= retry.max_attempts:
        return False
    if isinstance(exc, StreamRateLimitException):
        return not bool(getattr(exc, "unrecoverable", False))
    return isinstance(exc, StreamTransportException)


def _retry_delay(retry, exc, attempt: int) -> float:
    """Seconds to sleep before the next attempt: honors the server's
    ``Retry-After`` when present (clamped to ``max_backoff``), else full
    jitter over an exponential ceiling (``attempt`` is 0-indexed)."""
    retry_after = getattr(exc, "retry_after", None)
    if retry_after is not None and retry_after.total_seconds() > 0:
        return min(retry_after.total_seconds(), retry.max_backoff)
    ceil = min(retry.max_backoff, float(2**attempt))
    return random.uniform(0.0, ceil) if ceil > 0 else 0.0


def _resolve_pool_knobs(obj):
    """Pull the 3 pool knobs off ``obj`` if BaseStream has set them, else fall back to spec defaults. Top-level ``Stream``/``AsyncStream`` sets them on ``self`` before calling ``super().__init__()``, so a directly instantiated sub-client (or test fixture) still gets sane values.

    `is None` (not truthiness) so an explicit `0` / `0.0` from the caller is preserved rather than silently swapped for a default.
    """
    max_conns_per_host = getattr(obj, "max_conns_per_host", None)
    idle_timeout = getattr(obj, "idle_timeout", None)
    connect_timeout = getattr(obj, "connect_timeout", None)
    return (
        DEFAULT_MAX_CONNS_PER_HOST
        if max_conns_per_host is None
        else max_conns_per_host,
        DEFAULT_IDLE_TIMEOUT if idle_timeout is None else idle_timeout,
        DEFAULT_CONNECT_TIMEOUT if connect_timeout is None else connect_timeout,
    )


def _resolve_logger(obj) -> logging.Logger:
    """The caller's injected logger (``Stream``/``AsyncStream``'s ``logger=``
    kwarg, plumbed onto ``obj.log`` the same way as the pool knobs), or the
    shared module logger when none was passed."""
    return getattr(obj, "log", None) or logger


def _log_client_initialized(cfg, *, user_http_client: bool) -> None:
    """Emit the one-shot ``client.initialized`` event, replacing the old
    plain-text pool-config INFO line with the structured logging schema."""
    _resolve_logger(cfg).info(
        "client.initialized",
        extra={
            "stream.sdk.name": "stream-py",
            "stream.sdk.version": VERSION,
            "stream.client.max_conns_per_host": cfg.max_conns_per_host,
            "stream.client.idle_timeout_seconds": cfg.idle_timeout,
            "stream.client.connect_timeout_seconds": cfg.connect_timeout,
            "stream.client.request_timeout_seconds": cfg.timeout,
            "stream.client.gzip_enabled": not user_http_client,
            "stream.client.user_http_client": user_http_client,
            "stream.client.log_bodies": bool(getattr(cfg, "log_bodies", False)),
        },
    )


def _response_body_for_log(response: httpx.Response):
    """Redact a response body for the ``http.response.body`` log field.
    JSON bodies get the shallow key redaction; anything else (or anything
    that fails to parse as JSON) is passed through as text."""
    # Media types are case-insensitive; match application/json and any
    # structured +json type (e.g. application/problem+json) so their bodies
    # are redacted, not logged as raw text.
    content_type = response.headers.get("content-type", "").lower()
    if "application/json" in content_type or "+json" in content_type:
        try:
            return redact_json_body(json.loads(response.text))
        except (ValueError, TypeError):
            return response.text
    return response.text


def _read_file_bytes(file_path: str) -> bytes:
    with open(file_path, "rb") as f:
        return f.read()


def _strip_none(obj):
    """Recursively remove None values from dicts so unset optional fields
    are omitted from the JSON body instead of being sent as null."""
    if isinstance(obj, dict):
        return {k: _strip_none(v) for k, v in obj.items() if v is not None}
    if isinstance(obj, list):
        return [_strip_none(item) for item in obj]
    return obj


def build_path(path: str, path_params: Optional[Dict[str, Any]]) -> str:
    if path_params is None:
        return path
    for k, v in path_params.items():
        path_params[k] = quote(str(v), safe="")
    return path.format(**path_params)


class ResponseParserMixin:
    @with_span("parse_response")
    def _parse_response(
        self, response: httpx.Response, data_type: Type[T]
    ) -> StreamResponse[T]:
        if response.status_code >= 399:
            raise build_api_exception(response)

        try:
            parsed_result = json.loads(response.text) if response.text else {}

            data: T
            if hasattr(data_type, "from_dict"):
                from_dict = getattr(data_type, "from_dict")
                data = from_dict(parsed_result, infer_missing=True)
            elif get_origin(data_type) is not dict:
                raise AttributeError(f"{data_type.__name__} has no 'from_dict' method")
            else:
                data = cast(T, parsed_result)

        except (ValueError, AttributeError) as err:
            raise StreamApiException(response=response) from err

        return StreamResponse(response, data)


class TelemetryEndpointMixin(ABC):
    """
    Mixin that prepares request metadata for telemetry/tracing.

    Note for type-checkers/IDEs:
    - This mixin is designed to be used alongside clients that provide
      `base_url`, `api_key`, and an `_endpoint_name(path)` method
      (see `BaseClient` and `AsyncBaseClient`).
    - We declare these attributes here so static analysis tools understand
      they are available at runtime via the concrete client classes.
    """

    # Provided by BaseConfig in concrete clients
    base_url: Optional[str]
    api_key: Optional[str]

    # Provided by concrete clients (e.g. BaseClient/AsyncBaseClient)
    def _endpoint_name(self, path: str) -> str:  # pragma: no cover - interface hint
        raise NotImplementedError

    def _normalize_endpoint_from_path(self, path: str) -> str:
        # Convert /api/v2/video/call/{type}/{id} -> api.v2.video.call.$type.$id
        norm_parts = []
        for p in path.strip("/").split("/"):
            if not p:
                continue
            if p.startswith("{") and p.endswith("}"):
                name = p[1:-1].strip()
                if name:
                    norm_parts.append(f"${name}")
            else:
                norm_parts.append(p)
        return ".".join(norm_parts) if norm_parts else "root"

    def _prepare_request(self, method: str, path: str, query_params, kwargs):
        headers = kwargs.get("headers", {})
        path_params = kwargs.get("path_params") if kwargs else None
        url_path = (
            build_path(path, path_params) if path_params else build_path(path, None)
        )
        url_full = f"{self.base_url}{url_path}"
        endpoint = self._endpoint_name(path)
        client_request_id = str(uuid.uuid4())
        headers["x-client-request-id"] = client_request_id
        kwargs["headers"] = headers
        span_attrs = common_attributes(
            api_key=self.api_key,
            endpoint=endpoint,
            method=method,
            url=url_full,
            client_request_id=client_request_id,
        )
        # Enrich with contextual IDs when available (set by decorators)
        call_cid = get_current_call_cid()
        if call_cid:
            span_attrs["stream.call_cid"] = call_cid
        channel_cid = get_current_channel_cid()
        if channel_cid:
            span_attrs["stream.channel_cid"] = channel_cid
        return url_path, url_full, endpoint, span_attrs


class BaseClient(TelemetryEndpointMixin, BaseConfig, ResponseParserMixin, ABC):
    def __init__(
        self,
        api_key,
        base_url=None,
        token=None,
        timeout=None,
        user_agent=None,
    ):
        # The 3 pool knobs (max_conns_per_host, idle_timeout, connect_timeout) are set on ``self`` by BaseStream prior to this call when used via the top-level ``Stream``/``AsyncStream`` constructors. Sub-clients constructed directly use the spec defaults via _resolve_pool_knobs.
        max_conns_per_host, idle_timeout, connect_timeout = _resolve_pool_knobs(self)
        super().__init__(
            api_key=api_key,
            base_url=base_url,
            token=token,
            timeout=timeout,
            user_agent=user_agent,
            max_conns_per_host=max_conns_per_host,
            idle_timeout=idle_timeout,
            connect_timeout=connect_timeout,
        )
        http_client = getattr(self, "_http_client", None)
        if http_client is not None:
            if not isinstance(http_client, httpx.Client):
                raise TypeError(
                    f"http_client must be an httpx.Client instance, "
                    f"got {type(http_client).__name__}"
                )
            http_client.headers.update(self.headers)
            http_client.params = http_client.params.merge(self.params)
            http_client.base_url = self.base_url or ""
            if self.timeout is not None:
                http_client.timeout = httpx.Timeout(self.timeout)
            self.client = http_client
            self._owns_http_client = False
        else:
            limits = httpx.Limits(
                max_connections=self.max_conns_per_host,
                max_keepalive_connections=self.max_conns_per_host,
                keepalive_expiry=self.idle_timeout,
            )
            timeout_obj = httpx.Timeout(
                connect=self.connect_timeout,
                read=self.timeout,
                write=self.timeout,
                pool=self.timeout,
            )
            transport = getattr(self, "_transport", None)
            if transport is not None:
                self.client = httpx.Client(
                    base_url=self.base_url or "",
                    headers={**self.headers, "Accept-Encoding": "gzip"},
                    params=self.params,
                    timeout=timeout_obj,
                    limits=limits,
                    transport=transport,
                )
            else:
                self.client = httpx.Client(
                    base_url=self.base_url or "",
                    headers={**self.headers, "Accept-Encoding": "gzip"},
                    params=self.params,
                    timeout=timeout_obj,
                    limits=limits,
                )
            self._owns_http_client = True
        # The pool-config INFO line is emitted once by BaseStream after the
        # top-level client is built, not here, to avoid one line per
        # sub-client construction.

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()

    def _endpoint_name(self, path: str) -> str:
        op = getattr(self, "_operation_name", None)
        return op or current_operation(self._normalize_endpoint_from_path(path)) or ""

    def _attempt_sync(
        self,
        method: str,
        path: str,
        *,
        query_params=None,
        args=(),
        kwargs=None,
        data_type: Optional[Type[T]] = None,
    ):
        kwargs = kwargs or {}
        if "json" in kwargs and kwargs["json"] is not None:
            kwargs["json"] = _strip_none(kwargs["json"])
        url_path, url_full, endpoint, attrs = self._prepare_request(
            method, path, query_params, kwargs
        )
        log = _resolve_logger(self)
        log_bodies = bool(getattr(self, "log_bodies", False))
        sent_extra = {
            "http.request.method": method,
            "url.path": path,
            "url.query": redact_query(query_params) or "",
            "stream.endpoint_name": endpoint,
        }
        if log_bodies:
            sent_extra["http.request.body"] = redact_json_body(kwargs.get("json"))
        log.debug("http.request.sent", extra=sent_extra)

        start = time.perf_counter()
        # Span name uses logical operation (endpoint) rather than raw HTTP
        with span_request(
            endpoint, attributes=attrs, request_body=kwargs.get("json")
        ) as span:
            call_kwargs = dict(kwargs)
            call_kwargs.pop("path_params", None)
            try:
                response = getattr(self.client, method.lower())(
                    url_path, params=query_params, *args, **call_kwargs
                )
            except httpx.RequestError as err:
                # No failed-log here: the retry loop (_request_sync) owns
                # http.request.failed so it can log at DEBUG when retrying
                # and ERROR only on a final failure.
                raise wrap_transport_error(err) from err
            duration = parse_duration_from_body(response.content)
            if duration:
                span.set_attribute("http.server.duration", duration)
            try:
                span and span.set_attribute(
                    "http.response.status_code", response.status_code
                )
            except Exception:
                pass

            duration_ms = (time.perf_counter() - start) * 1000.0
            received_extra = {
                "http.request.method": method,
                "url.path": path,
                "stream.endpoint_name": endpoint,
                "http.response.status_code": response.status_code,
                "http.response.body.size": len(response.content or b""),
                "duration_ms": int(duration_ms),
            }
            if log_bodies:
                received_extra["http.response.body"] = _response_body_for_log(response)
            log.debug("http.response.received", extra=received_extra)
            # Metrics should be low-cardinality: exclude url/call_cid/channel_cid
            metric_attrs = metric_attributes(
                api_key=self.api_key,
                endpoint=endpoint,
                method=method,
                status_code=getattr(response, "status_code", None),
            )
            record_metrics(duration_ms, attributes=metric_attrs)
            return self._parse_response(response, data_type or Dict[str, Any])

    def _request_sync(
        self,
        method: str,
        path: str,
        *,
        query_params=None,
        args=(),
        kwargs=None,
        data_type: Optional[Type[T]] = None,
    ):
        """Retry loop around ``_attempt_sync``. Disabled (default) retry
        policy means exactly one attempt, errors surface unchanged. When
        enabled, retries GET/HEAD on HTTP 429 / transport errors per
        ``_retry_eligible``/``_retry_delay``, owning the ``http.request.failed``
        log level so a retried failure logs at DEBUG and only a final
        transport failure logs at ERROR (a final 429 is already covered by
        ``http.response.received``)."""
        retry = getattr(self, "retry", None)
        log = _resolve_logger(self)
        endpoint = self._endpoint_name(path)
        attempt = 0
        while True:
            t0 = time.perf_counter()
            try:
                return self._attempt_sync(
                    method,
                    path,
                    query_params=query_params,
                    args=args,
                    kwargs=kwargs,
                    data_type=data_type,
                )
            except (StreamRateLimitException, StreamTransportException) as exc:
                duration_ms = int((time.perf_counter() - t0) * 1000)
                if _retry_eligible(retry, exc, method, attempt):
                    delay = _retry_delay(retry, exc, attempt)
                    extra = {
                        "http.request.method": method,
                        "url.path": path,
                        "stream.endpoint_name": endpoint,
                        "retry.attempt": attempt + 1,
                        "backoff_seconds": round(delay, 3),
                        "error.message": str(exc.__cause__ or exc),
                        "duration_ms": duration_ms,
                    }
                    if isinstance(exc, StreamTransportException):
                        extra["error.type"] = exc.error_type
                    log.debug("http.request.failed", extra=extra)
                    time.sleep(delay)
                    attempt += 1
                    continue
                if isinstance(exc, StreamTransportException):
                    log.error(
                        "http.request.failed",
                        extra={
                            "http.request.method": method,
                            "url.path": path,
                            "stream.endpoint_name": endpoint,
                            "retry.attempt": attempt + 1,
                            "error.type": exc.error_type,
                            "error.message": str(exc.__cause__ or exc),
                            "duration_ms": duration_ms,
                        },
                    )
                raise

    def patch(
        self,
        path,
        data_type: Optional[Type[T]] = None,
        path_params: Optional[Dict[str, str]] = None,
        query_params: Optional[Dict[str, str]] = None,
        *args,
        **kwargs,
    ) -> StreamResponse[T]:
        return self._request_sync(
            "PATCH",
            path,
            query_params=query_params,
            args=args,
            kwargs=kwargs | {"path_params": path_params},
            data_type=data_type,
        )

    def get(
        self,
        path,
        data_type: Optional[Type[T]] = None,
        path_params: Optional[Dict[str, str]] = None,
        query_params: Optional[Dict[str, str]] = None,
        *args,
        **kwargs,
    ) -> StreamResponse[T]:
        return self._request_sync(
            "GET",
            path,
            query_params=query_params,
            args=args,
            kwargs=kwargs | {"path_params": path_params},
            data_type=data_type,
        )

    def post(
        self,
        path,
        data_type: Optional[Type[T]] = None,
        path_params: Optional[Dict[str, str]] = None,
        query_params: Optional[Dict[str, str]] = None,
        *args,
        **kwargs,
    ) -> StreamResponse[T]:
        return self._request_sync(
            "POST",
            path,
            query_params=query_params,
            args=args,
            kwargs=kwargs | {"path_params": path_params},
            data_type=data_type,
        )

    def put(
        self,
        path,
        data_type: Optional[Type[T]] = None,
        path_params: Optional[Dict[str, str]] = None,
        query_params: Optional[Dict[str, str]] = None,
        *args,
        **kwargs,
    ) -> StreamResponse[T]:
        return self._request_sync(
            "PUT",
            path,
            query_params=query_params,
            args=args,
            kwargs=kwargs | {"path_params": path_params},
            data_type=data_type,
        )

    def delete(
        self,
        path,
        data_type: Optional[Type[T]] = None,
        path_params: Optional[Dict[str, str]] = None,
        query_params: Optional[Dict[str, str]] = None,
        *args,
        **kwargs,
    ) -> StreamResponse[T]:
        return self._request_sync(
            "DELETE",
            path,
            query_params=query_params,
            args=args,
            kwargs=kwargs | {"path_params": path_params},
            data_type=data_type,
        )

    def _upload_multipart(
        self,
        path: str,
        data_type: Type[T],
        file_path: str,
        *,
        path_params: Optional[Dict[str, str]] = None,
        query_params: Optional[Dict[str, str]] = None,
        form_fields: Optional[List[Tuple[str, str]]] = None,
    ) -> StreamResponse[T]:
        """Send a multipart/form-data upload request, matching Go/PHP SDK behavior."""
        file_name = os.path.basename(file_path)
        content_type = mimetypes.guess_type(file_path)[0] or "application/octet-stream"
        with open(file_path, "rb") as f:
            file_content = f.read()

        files = {"file": (file_name, file_content, content_type)}
        data: Dict[str, str] = {}
        for field_name, field_value in form_fields or []:
            data[field_name] = field_value

        kwargs: Dict[str, Any] = {"files": files}
        if data:
            kwargs["data"] = data

        return self._request_sync(
            "POST",
            path,
            query_params=query_params,
            kwargs=kwargs | {"path_params": path_params},
            data_type=data_type,
        )

    def close(self):
        """
        Close HTTPX client.

        If the client was provided externally via ``http_client``, this is a
        no-op; the caller that created the client is responsible for closing
        it.
        """
        if getattr(self, "_owns_http_client", True):
            self.client.close()


class AsyncBaseClient(TelemetryEndpointMixin, BaseConfig, ResponseParserMixin, ABC):
    def __init__(
        self,
        api_key,
        base_url=None,
        token=None,
        timeout=None,
        user_agent=None,
    ):
        # The 3 pool knobs (max_conns_per_host, idle_timeout, connect_timeout) are set on ``self`` by BaseStream prior to this call when used via the top-level ``Stream``/``AsyncStream`` constructors. Sub-clients constructed directly use the spec defaults via _resolve_pool_knobs.
        max_conns_per_host, idle_timeout, connect_timeout = _resolve_pool_knobs(self)
        super().__init__(
            api_key=api_key,
            base_url=base_url,
            token=token,
            timeout=timeout,
            user_agent=user_agent,
            max_conns_per_host=max_conns_per_host,
            idle_timeout=idle_timeout,
            connect_timeout=connect_timeout,
        )
        http_client = getattr(self, "_http_client", None)
        if http_client is not None:
            if not isinstance(http_client, httpx.AsyncClient):
                raise TypeError(
                    f"http_client must be an httpx.AsyncClient instance, "
                    f"got {type(http_client).__name__}"
                )
            http_client.headers.update(self.headers)
            http_client.params = http_client.params.merge(self.params)
            http_client.base_url = self.base_url or ""
            if self.timeout is not None:
                http_client.timeout = httpx.Timeout(self.timeout)
            self.client = http_client
            self._owns_http_client = False
        else:
            limits = httpx.Limits(
                max_connections=self.max_conns_per_host,
                max_keepalive_connections=self.max_conns_per_host,
                keepalive_expiry=self.idle_timeout,
            )
            timeout_obj = httpx.Timeout(
                connect=self.connect_timeout,
                read=self.timeout,
                write=self.timeout,
                pool=self.timeout,
            )
            transport = getattr(self, "_transport", None)
            if transport is not None:
                self.client = httpx.AsyncClient(
                    base_url=self.base_url or "",
                    headers={**self.headers, "Accept-Encoding": "gzip"},
                    params=self.params,
                    timeout=timeout_obj,
                    limits=limits,
                    transport=transport,
                )
            else:
                self.client = httpx.AsyncClient(
                    base_url=self.base_url or "",
                    headers={**self.headers, "Accept-Encoding": "gzip"},
                    params=self.params,
                    timeout=timeout_obj,
                    limits=limits,
                )
            self._owns_http_client = True
        # The pool-config INFO line is emitted once by BaseStream after the
        # top-level client is built, not here, to avoid one line per
        # sub-client construction.

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.aclose()

    async def aclose(self):
        """Close HTTPX async client (closes pools/keep-alives).

        If the client was provided externally via ``http_client``, this is a
        no-op; the caller that created the client is responsible for closing
        it.
        """
        if getattr(self, "_owns_http_client", True):
            await self.client.aclose()

    async def _upload_multipart(
        self,
        path: str,
        data_type: Type[T],
        file_path: str,
        *,
        path_params: Optional[Dict[str, str]] = None,
        query_params: Optional[Dict[str, str]] = None,
        form_fields: Optional[List[Tuple[str, str]]] = None,
    ) -> StreamResponse[T]:
        """Send a multipart/form-data upload request, matching Go/PHP SDK behavior."""
        file_name = os.path.basename(file_path)
        content_type = mimetypes.guess_type(file_path)[0] or "application/octet-stream"

        file_content = await asyncio.to_thread(_read_file_bytes, file_path)

        files = {"file": (file_name, file_content, content_type)}
        data: Dict[str, str] = {}
        for field_name, field_value in form_fields or []:
            data[field_name] = field_value

        kwargs: Dict[str, Any] = {"files": files}
        if data:
            kwargs["data"] = data

        return await self._request_async(
            "POST",
            path,
            query_params=query_params,
            kwargs=kwargs | {"path_params": path_params},
            data_type=data_type,
        )

    def _endpoint_name(self, path: str) -> str:
        op = getattr(self, "_operation_name", None)
        return op or current_operation(self._normalize_endpoint_from_path(path)) or ""

    async def _attempt_async(
        self,
        method: str,
        path: str,
        *,
        query_params=None,
        args=(),
        kwargs=None,
        data_type: Optional[Type[T]] = None,
    ):
        kwargs = kwargs or {}
        if "json" in kwargs and kwargs["json"] is not None:
            kwargs["json"] = _strip_none(kwargs["json"])
        query_params = query_params or {}
        url_path, url_full, endpoint, attrs = self._prepare_request(
            method, path, query_params, kwargs
        )
        log = _resolve_logger(self)
        log_bodies = bool(getattr(self, "log_bodies", False))
        sent_extra = {
            "http.request.method": method,
            "url.path": path,
            "url.query": redact_query(query_params) or "",
            "stream.endpoint_name": endpoint,
        }
        if log_bodies:
            sent_extra["http.request.body"] = redact_json_body(kwargs.get("json"))
        log.debug("http.request.sent", extra=sent_extra)

        start = time.perf_counter()
        with span_request(
            endpoint, attributes=attrs, request_body=kwargs.get("json")
        ) as span:
            call_kwargs = dict(kwargs)
            call_kwargs.pop("path_params", None)

            if call_kwargs.get("json") is not None:
                json_body = call_kwargs.pop("json")
                json_str = await asyncio.to_thread(json.dumps, json_body)
                call_kwargs["content"] = json_str
                call_kwargs["headers"] = call_kwargs.get("headers", {})
                call_kwargs["headers"]["Content-Type"] = "application/json"

            try:
                response = await getattr(self.client, method.lower())(
                    url_path, params=query_params, *args, **call_kwargs
                )
            except httpx.RequestError as err:
                # No failed-log here: the retry loop (_request_async) owns
                # http.request.failed so it can log at DEBUG when retrying
                # and ERROR only on a final failure.
                raise wrap_transport_error(err) from err
            duration = parse_duration_from_body(response.content)
            if duration:
                span.set_attribute("http.server.duration", duration)
            try:
                span and span.set_attribute(
                    "http.response.status_code", response.status_code
                )
            except Exception:
                pass

            duration_ms = (time.perf_counter() - start) * 1000.0
            received_extra = {
                "http.request.method": method,
                "url.path": path,
                "stream.endpoint_name": endpoint,
                "http.response.status_code": response.status_code,
                "http.response.body.size": len(response.content or b""),
                "duration_ms": int(duration_ms),
            }
            if log_bodies:
                received_extra["http.response.body"] = await asyncio.to_thread(
                    _response_body_for_log, response
                )
            log.debug("http.response.received", extra=received_extra)
            # Metrics should be low-cardinality: exclude url/call_cid/channel_cid
            metric_attrs = metric_attributes(
                api_key=self.api_key,
                endpoint=endpoint,
                method=method,
                status_code=getattr(response, "status_code", None),
            )
            record_metrics(duration_ms, attributes=metric_attrs)
            return await asyncio.to_thread(
                self._parse_response, response, data_type or Dict[str, Any]
            )

    async def _request_async(
        self,
        method: str,
        path: str,
        *,
        query_params=None,
        args=(),
        kwargs=None,
        data_type: Optional[Type[T]] = None,
    ):
        """Async twin of ``BaseClient._request_sync``; see that docstring."""
        retry = getattr(self, "retry", None)
        log = _resolve_logger(self)
        endpoint = self._endpoint_name(path)
        attempt = 0
        while True:
            t0 = time.perf_counter()
            try:
                return await self._attempt_async(
                    method,
                    path,
                    query_params=query_params,
                    args=args,
                    kwargs=kwargs,
                    data_type=data_type,
                )
            except (StreamRateLimitException, StreamTransportException) as exc:
                duration_ms = int((time.perf_counter() - t0) * 1000)
                if _retry_eligible(retry, exc, method, attempt):
                    delay = _retry_delay(retry, exc, attempt)
                    extra = {
                        "http.request.method": method,
                        "url.path": path,
                        "stream.endpoint_name": endpoint,
                        "retry.attempt": attempt + 1,
                        "backoff_seconds": round(delay, 3),
                        "error.message": str(exc.__cause__ or exc),
                        "duration_ms": duration_ms,
                    }
                    if isinstance(exc, StreamTransportException):
                        extra["error.type"] = exc.error_type
                    log.debug("http.request.failed", extra=extra)
                    await asyncio.sleep(delay)
                    attempt += 1
                    continue
                if isinstance(exc, StreamTransportException):
                    log.error(
                        "http.request.failed",
                        extra={
                            "http.request.method": method,
                            "url.path": path,
                            "stream.endpoint_name": endpoint,
                            "retry.attempt": attempt + 1,
                            "error.type": exc.error_type,
                            "error.message": str(exc.__cause__ or exc),
                            "duration_ms": duration_ms,
                        },
                    )
                raise

    async def patch(
        self,
        path,
        data_type: Optional[Type[T]] = None,
        path_params: Optional[Dict[str, str]] = None,
        query_params: Optional[Dict[str, str]] = None,
        *args,
        **kwargs,
    ) -> StreamResponse[T]:
        return await self._request_async(
            "PATCH",
            path,
            query_params=query_params,
            args=args,
            kwargs=kwargs | {"path_params": path_params},
            data_type=data_type,
        )

    async def get(
        self,
        path,
        data_type: Optional[Type[T]] = None,
        path_params: Optional[Dict[str, str]] = None,
        query_params: Optional[Dict[str, str]] = None,
        *args,
        **kwargs,
    ) -> StreamResponse[T]:
        return await self._request_async(
            "GET",
            path,
            query_params=query_params,
            args=args,
            kwargs=kwargs | {"path_params": path_params},
            data_type=data_type,
        )

    async def post(
        self,
        path,
        data_type: Optional[Type[T]] = None,
        path_params: Optional[Dict[str, str]] = None,
        query_params: Optional[Dict[str, str]] = None,
        *args,
        **kwargs,
    ) -> StreamResponse[T]:
        return await self._request_async(
            "POST",
            path,
            query_params=query_params,
            args=args,
            kwargs=kwargs | {"path_params": path_params},
            data_type=data_type,
        )

    async def put(
        self,
        path,
        data_type: Optional[Type[T]] = None,
        path_params: Optional[Dict[str, str]] = None,
        query_params: Optional[Dict[str, str]] = None,
        *args,
        **kwargs,
    ) -> StreamResponse[T]:
        return await self._request_async(
            "PUT",
            path,
            query_params=query_params,
            args=args,
            kwargs=kwargs | {"path_params": path_params},
            data_type=data_type,
        )

    async def delete(
        self,
        path,
        data_type: Optional[Type[T]] = None,
        path_params: Optional[Dict[str, str]] = None,
        query_params: Optional[Dict[str, str]] = None,
        *args,
        **kwargs,
    ) -> StreamResponse[T]:
        return await self._request_async(
            "DELETE",
            path,
            query_params=query_params,
            args=args,
            kwargs=kwargs | {"path_params": path_params},
            data_type=data_type,
        )


def __getattr__(name: str):
    """StreamApiException is exported under its new name; resolve here lazily and warn once."""
    if name == "StreamAPIException":
        warnings.warn(
            "getstream.base.StreamAPIException is deprecated; import "
            "StreamApiException from getstream (or getstream.exceptions) "
            "instead. The legacy alias will be removed one minor cycle after "
            "this release.",
            DeprecationWarning,
            stacklevel=2,
        )
        return StreamApiException
    raise AttributeError(f"module 'getstream.base' has no attribute {name!r}")


def parse_duration_from_body(body: bytes) -> Optional[str]:
    try:
        for prefix, event, value in ijson.parse(body):
            if prefix == "duration" and event == "string":
                return value
    except (ijson.common.IncompleteJSONError, ijson.common.JSONError):
        pass
    return None
