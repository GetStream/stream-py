import httpx
from getstream.config import BaseConfig


class BaseClientAsync(BaseConfig):
    def __init__(self, api_key, base_url=None, anonymous=False, token=None):
        super().__init__(api_key, base_url, anonymous, token)
        self.client = httpx.AsyncClient(
            base_url=self.base_url, headers=self.headers, params=self.params
        )

    async def get(self, path, *args, **kwargs):
        async with self.client as client:
            return await client.get(path, *args, **kwargs)

    async def post(self, path, *args, **kwargs):
        async with self.client as client:
            return await client.post(path, *args, **kwargs)

    async def put(self, path, *args, **kwargs):
        async with self.client as client:
            return await client.put(path, *args, **kwargs)

    async def delete(self, path, *args, **kwargs):
        async with self.client as client:
            return await client.delete(path, *args, **kwargs)
