import json
import time
import uuid
import asyncio
from typing import Any, Dict, Optional, Type, cast, get_origin

from getstream.models import APIError
from getstream.rate_limit import extract_rate_limit
from getstream.stream_response import StreamResponse
from getstream.generic import T
import httpx
from getstream.config import BaseConfig
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
            raise StreamAPIException(
                response=response,
            )

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

        except ValueError:
            raise StreamAPIException(
                response=response,
            )

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
        super().__init__(
            api_key=api_key,
            base_url=base_url,
            token=token,
            timeout=timeout,
            user_agent=user_agent,
        )
        self.client = httpx.Client(
            base_url=self.base_url or "",
            headers=self.headers,
            params=self.params,
            timeout=httpx.Timeout(self.timeout),
        )

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()

    def _endpoint_name(self, path: str) -> str:
        op = getattr(self, "_operation_name", None)
        return op or current_operation(self._normalize_endpoint_from_path(path)) or ""

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
        kwargs = kwargs or {}
        url_path, url_full, endpoint, attrs = self._prepare_request(
            method, path, query_params, kwargs
        )
        start = time.perf_counter()
        # Span name uses logical operation (endpoint) rather than raw HTTP
        with span_request(
            endpoint, attributes=attrs, request_body=kwargs.get("json")
        ) as span:
            call_kwargs = dict(kwargs)
            call_kwargs.pop("path_params", None)
            response = getattr(self.client, method.lower())(
                url_path, params=query_params, *args, **call_kwargs
            )
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
            # Metrics should be low-cardinality: exclude url/call_cid/channel_cid
            metric_attrs = metric_attributes(
                api_key=self.api_key,
                endpoint=endpoint,
                method=method,
                status_code=getattr(response, "status_code", None),
            )
            record_metrics(duration_ms, attributes=metric_attrs)
            return self._parse_response(response, data_type or Dict[str, Any])

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

    def close(self):
        """
        Close HTTPX client.
        """
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
        super().__init__(
            api_key=api_key,
            base_url=base_url,
            token=token,
            timeout=timeout,
            user_agent=user_agent,
        )
        self.client = httpx.AsyncClient(
            base_url=self.base_url or "",
            headers=self.headers,
            params=self.params,
            timeout=httpx.Timeout(self.timeout),
        )

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.aclose()

    async def aclose(self):
        """Close HTTPX async client (closes pools/keep-alives)."""
        await self.client.aclose()

    def _endpoint_name(self, path: str) -> str:
        op = getattr(self, "_operation_name", None)
        return op or current_operation(self._normalize_endpoint_from_path(path)) or ""

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
        kwargs = kwargs or {}
        query_params = query_params or {}
        url_path, url_full, endpoint, attrs = self._prepare_request(
            method, path, query_params, kwargs
        )
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

            response = await getattr(self.client, method.lower())(
                url_path, params=query_params, *args, **call_kwargs
            )
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


class StreamAPIException(Exception):
    """
    A custom exception for handling errors from a Stream API response.

    This exception is raised when an API call encounters an issue, providing
    detailed information from the HTTP response. It attempts to parse the response
    content into a structured API error. If the response content is not JSON or
    lacks the expected structure, it will simply report the HTTP status code.

    Attributes:
        api_error (Optional[APIError]): An optional APIError object that is
            populated if the response content contains structured error information.
        rate_limit_info (RateLimitInfo): Information about the API's rate limiting
            controls extracted from the response headers.
        http_response (httpx.Response): The full HTTP response object from httpx.
        status_code (int): The HTTP status code from the response.

    Args:
        response (httpx.Response): The HTTP response received from the Stream API.

    Raises:
        ValueError: If the response content cannot be parsed into JSON, indicating
            that the server's response was not in the expected format.
    """

    def __init__(self, response: httpx.Response) -> None:
        self.api_error: Optional[APIError] = None
        self.rate_limit_info = extract_rate_limit(response)
        self.http_response = response
        self.status_code = response.status_code

        try:
            parsed_response: Dict = json.loads(response.content)
            self.api_error = APIError.from_dict(parsed_response)
        except ValueError:
            pass

    def __str__(self) -> str:
        if self.api_error:
            return f'Stream error code {self.api_error.code}: {self.api_error.message}"'
        else:
            return f"Stream error HTTP code: {self.status_code}"


def parse_duration_from_body(body: bytes) -> Optional[str]:
    for prefix, event, value in ijson.parse(body):
        if prefix == "duration" and event == "string":
            return value
    return None
