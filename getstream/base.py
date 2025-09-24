import json
from typing import Any, Dict, Optional, Type, get_origin

from getstream.models import APIError
from getstream.rate_limit import extract_rate_limit
from getstream.stream_response import StreamResponse
from getstream.generic import T
import httpx
from getstream.config import BaseConfig
from urllib.parse import quote
from abc import ABC


def build_path(path: str, path_params: dict) -> str:
    if path_params is None:
        return path
    for k, v in path_params.items():
        path_params[k] = quote(str(v), safe="")
    return path.format(**path_params)


class ResponseParserMixin:
    def _parse_response(
        self, response: httpx.Response, data_type: Type[T]
    ) -> StreamResponse[T]:
        if response.status_code >= 399:
            raise StreamAPIException(
                response=response,
            )

        try:
            parsed_result = json.loads(response.text) if response.text else {}

            if hasattr(data_type, "from_dict"):
                data = data_type.from_dict(parsed_result, infer_missing=True)
            elif get_origin(data_type) is not dict:
                raise AttributeError(f"{data_type.__name__} has no 'from_dict' method")
            else:
                data = parsed_result

        except ValueError:
            raise StreamAPIException(
                response=response,
            )

        return StreamResponse(response, data)


class BaseClient(BaseConfig, ResponseParserMixin, ABC):
    def __init__(
        self,
        api_key,
        base_url=None,
        token=None,
        timeout=None,
    ):
        super().__init__(
            api_key=api_key,
            base_url=base_url,
            token=token,
            timeout=timeout,
        )
        self.client = httpx.Client(
            base_url=self.base_url,
            headers=self.headers,
            params=self.params,
            timeout=httpx.Timeout(self.timeout),
        )

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()

    def patch(
        self,
        path,
        data_type: Optional[Type[T]] = None,
        path_params: Optional[Dict[str, str]] = None,
        query_params: Optional[Dict[str, str]] = None,
        *args,
        **kwargs,
    ) -> StreamResponse[T]:
        response = self.client.patch(
            build_path(path, path_params), params=query_params, *args, **kwargs
        )
        return self._parse_response(response, data_type or Dict[str, Any])

    def get(
        self,
        path,
        data_type: Optional[Type[T]] = None,
        path_params: Optional[Dict[str, str]] = None,
        query_params: Optional[Dict[str, str]] = None,
        *args,
        **kwargs,
    ) -> StreamResponse[T]:
        response = self.client.get(
            build_path(path, path_params), params=query_params, *args, **kwargs
        )
        return self._parse_response(response, data_type or Dict[str, Any])

    def post(
        self,
        path,
        data_type: Optional[Type[T]] = None,
        path_params: Optional[Dict[str, str]] = None,
        query_params: Optional[Dict[str, str]] = None,
        *args,
        **kwargs,
    ) -> StreamResponse[T]:
        response = self.client.post(
            build_path(path, path_params), params=query_params, *args, **kwargs
        )

        return self._parse_response(response, data_type or Dict[str, Any])

    def put(
        self,
        path,
        data_type: Optional[Type[T]] = None,
        path_params: Optional[Dict[str, str]] = None,
        query_params: Optional[Dict[str, str]] = None,
        *args,
        **kwargs,
    ) -> StreamResponse[T]:
        response = self.client.put(
            build_path(path, path_params), params=query_params, *args, **kwargs
        )
        return self._parse_response(response, data_type or Dict[str, Any])

    def delete(
        self,
        path,
        data_type: Optional[Type[T]] = None,
        path_params: Optional[Dict[str, str]] = None,
        query_params: Optional[Dict[str, str]] = None,
        *args,
        **kwargs,
    ) -> StreamResponse[T]:
        response = self.client.delete(
            build_path(path, path_params), params=query_params, *args, **kwargs
        )
        return self._parse_response(response, data_type or Dict[str, Any])

    def close(self):
        """
        Close HTTPX client.
        """
        self.client.close()


class AsyncBaseClient(BaseConfig, ResponseParserMixin, ABC):
    def __init__(
        self,
        api_key,
        base_url=None,
        token=None,
        timeout=None,
    ):
        super().__init__(
            api_key=api_key,
            base_url=base_url,
            token=token,
            timeout=timeout,
        )
        self.client = httpx.AsyncClient(
            base_url=self.base_url,
            headers=self.headers,
            params=self.params,
            timeout=httpx.Timeout(self.timeout),
        )

    def __aenter__(self):
        return self

    def __aexit__(self, exc_type, exc_val, exc_tb):
        self.close()

    async def aclose(self):
        """Close HTTPX async client (closes pools/keep-alives)."""
        await self.client.aclose()

    async def patch(
        self,
        path,
        data_type: Optional[Type[T]] = None,
        path_params: Optional[Dict[str, str]] = None,
        query_params: Optional[Dict[str, str]] = None,
        *args,
        **kwargs,
    ) -> StreamResponse[T]:
        response = await self.client.patch(
            build_path(path, path_params), params=query_params, *args, **kwargs
        )
        return self._parse_response(response, data_type or Dict[str, Any])

    async def get(
        self,
        path,
        data_type: Optional[Type[T]] = None,
        path_params: Optional[Dict[str, str]] = None,
        query_params: Optional[Dict[str, str]] = None,
        *args,
        **kwargs,
    ) -> StreamResponse[T]:
        response = await self.client.get(
            build_path(path, path_params), params=query_params, *args, **kwargs
        )
        return self._parse_response(response, data_type or Dict[str, Any])

    async def post(
        self,
        path,
        data_type: Optional[Type[T]] = None,
        path_params: Optional[Dict[str, str]] = None,
        query_params: Optional[Dict[str, str]] = None,
        *args,
        **kwargs,
    ) -> StreamResponse[T]:
        response = await self.client.post(
            build_path(path, path_params), params=query_params, *args, **kwargs
        )

        return self._parse_response(response, data_type or Dict[str, Any])

    async def put(
        self,
        path,
        data_type: Optional[Type[T]] = None,
        path_params: Optional[Dict[str, str]] = None,
        query_params: Optional[Dict[str, str]] = None,
        *args,
        **kwargs,
    ) -> StreamResponse[T]:
        response = await self.client.put(
            build_path(path, path_params), params=query_params, *args, **kwargs
        )
        return self._parse_response(response, data_type or Dict[str, Any])

    async def delete(
        self,
        path,
        data_type: Optional[Type[T]] = None,
        path_params: Optional[Dict[str, str]] = None,
        query_params: Optional[Dict[str, str]] = None,
        *args,
        **kwargs,
    ) -> StreamResponse[T]:
        response = await self.client.delete(
            build_path(path, path_params), params=query_params, *args, **kwargs
        )
        return self._parse_response(response, data_type or Dict[str, Any])


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
