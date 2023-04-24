import httpx
from getstream.config import BaseConfig


class BaseClient(BaseConfig):
    def __init__(self, api_key, base_url=None, anonymous=False, token=None):
        super().__init__(
            api_key=api_key, base_url=base_url, anonymous=anonymous, token=token
        )
        self.client = httpx.Client(
            base_url=self.base_url, headers=self.headers, params=self.params
        )

    def get(self, path, *args, **kwargs):
        with self.client as client:
            return client.get(path, *args, **kwargs)

    def post(self, path, *args, **kwargs):
        with self.client as client:
            return client.post(path, *args, **kwargs)

    def put(self, path, *args, **kwargs):
        with self.client as client:
            return client.put(path, *args, **kwargs)

    def delete(self, path, *args, **kwargs):
        with self.client as client:
            return client.delete(path, *args, **kwargs)
