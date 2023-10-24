import json
from typing import Any, Dict, Optional, Type, get_origin
from getstream.stream_response import StreamResponse
from getstream.generic import T
from getstream.video.exceptions import StreamAPIException
import httpx
from getstream.config import BaseConfig
from urllib.parse import quote
from abc import ABC


def build_path(path: str, path_params: dict) -> str:
    for k, v in path_params.items():
        path_params[k] = quote(
            v, safe=""
        )  # in case of special characters in the path. Known cases: chat message ids.

    return path.format(**path_params)


class BaseClient(BaseConfig, ABC):
    def __init__(
        self,
        api_key,
        base_url=None,
        anonymous=False,
        token=None,
        timeout=None,
        user_agent=None,
    ):
        super().__init__(
            api_key=api_key,
            base_url=base_url,
            anonymous=anonymous,
            token=token,
            timeout=timeout,
            user_agent=user_agent,
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
                data = data_type.from_dict(parsed_result)
            elif get_origin(data_type) is not dict:
                raise AttributeError(f"{data_type.__name__} has no 'from_dict' method")
            else:
                data = parsed_result

        except ValueError:
            raise StreamAPIException(
                response=response,
            )

        return StreamResponse(response, data)

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
        self.client.close()
