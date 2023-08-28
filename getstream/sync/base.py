import json
from typing import Any, Dict, Optional, Type
from getstream.stream_response import StreamResponse
from getstream.generic import T
from getstream.video.exceptions import StreamAPIException
import httpx
from getstream.config import BaseConfig


class BaseClient(BaseConfig):
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
                text=f"Request failed with status code {response.status_code}: {response.text}",
                status_code=response.status_code,
            )

        try:
            parsed_result = json.loads(response.text) if response.text else {}
            if callable(getattr(data_type, "from_dict", None)):
                data = data_type.from_dict(parsed_result)
            else:
                raise AttributeError(f"{data_type.__name__} has no 'from_dict' method")

        except ValueError:
            raise StreamAPIException(
                text=f"Response body is not valid JSON: {response.text}",
                status_code=response.status_code,
            )

        return StreamResponse(response, data)

    def get(
        self, path, data_type: Optional[Type[T]] = None, *args, **kwargs
    ) -> StreamResponse[T]:
        response = self.client.get(path, *args, **kwargs)
        return self._parse_response(response, data_type or Dict[str, Any])

    def post(
        self,
        path,
        data_type: Optional[Type[T]] = None,
        *args,
        **kwargs,
    ) -> StreamResponse[T]:
        response = self.client.post(path, *args, **kwargs)
        return self._parse_response(response, data_type or Dict[str, Any])

    def put(
        self,
        path,
        data_type: Optional[Type[T]] = None,
        *args,
        **kwargs,
    ) -> StreamResponse[T]:
        response = self.client.put(path, *args, **kwargs)
        return self._parse_response(response, data_type or Dict[str, Any])

    def delete(
        self, path, data_type: Optional[Type[T]] = None, *args, **kwargs
    ) -> StreamResponse[T]:
        response = self.client.delete(path, *args, **kwargs)
        return self._parse_response(response, data_type or Dict[str, Any])

    def close(self):
        self.client.close()
