import httpx

from stream.version import VERSION


class BaseClient:
    def __init__(self, token, base_url):
        self.token = token

        self.base_url = base_url
        self.client = httpx.AsyncClient(base_url=self.base_url)
        self.anonymous = False

    def get_user_agent(self):
        return f"stream-python-client-{VERSION}"

    def get_auth_type(self):
        if self.anonymous:
            return "anonymous"
        else:
            return "jwt"

    async def config(self, headers=None):
        headers = headers or {}

        if self.token is not None:
            headers["Authorization"] = self.token

        headers["stream-auth-type"] = self.get_auth_type()
        headers["X-Stream-Client"] = self.get_user_agent()
        config = {
            "headers": headers,
        }
        return config

    def format_url(self, path):
        # concatenate base url and path
        return f"{self.base_url}/{path}"

    async def get(self, path, params=None, headers=None):
        config = await self.config(headers)
        return await self.client.get(self.format_url(path), params=params, **config)

    async def post(
        self, path, data=None, json=None, params=None, files=None, headers=None
    ):
        config = await self.config(headers)
        return await self.client.post(
            self.format_url(path),
            json=json,
            data=data,
            files=files,
            params=params,
            **config,
        )

    async def put(
        self,
        path,
        json=None,
        data=None,
        content=None,
        files=None,
        params=None,
        headers=None,
    ):
        config = await self.config(path, headers)
        return await self.client.put(
            self.format_url(path),
            json=json,
            data=data,
            content=content,
            files=files,
            params=params,
            **config,
        )

    async def delete(self, path, headers=None, config=None):
        config = await self.config(path, headers)
        return await self.client.delete(self.format_url(path), **config)
