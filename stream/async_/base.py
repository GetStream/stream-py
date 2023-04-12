import httpx

from stream.version import VERSION


class BaseClientAsync:
    def __init__(self, base_url=None, anonymous=False, token=None):
        self.anonymous = anonymous
        headers = headers or {}
        if token is not None:
            headers["Authorization"] = self.token
        headers["stream-auth-type"] = self._get_user_agent()
        headers["X-Stream-Client"] = self._get_user_agent()
        self.client = httpx.AsyncClient(base_url=base_url, headers=headers)

    def _get_user_agent(self):
        return f"stream-python-client-{VERSION}"

    def _get_auth_type(self):
        if self.anonymous:
            return "anonymous"
        else:
            return "jwt"

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
