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

    def get(self, path, *args, **kwargs):
        return self.client.get(path, *args, **kwargs)

    def post(self, path, *args, **kwargs):
        return self.client.post(path, *args, **kwargs)

    def put(self, path, *args, **kwargs):
        return self.client.put(path, *args, **kwargs)

    def delete(self, path, *args, **kwargs):
        return self.client.delete(path, *args, **kwargs)

    def close(self):
        self.client.close()
