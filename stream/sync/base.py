import httpx

from stream.version import VERSION


class BaseClient:
    def __init__(self, api_key, base_url, token=None, anonymous=False):
        print(base_url)
        self.anonymous = anonymous
        headers = {}
        if token is not None:
            headers["Authorization"] = token
        headers["stream-auth-type"] = self._get_auth_type()
        headers["X-Stream-Client"] = self._get_user_agent()
        self.client = httpx.Client(
            base_url=base_url, headers=headers, params={"api_key": api_key}
        )

    def _get_user_agent(self):
        return f"stream-python-client-{VERSION}"

    def _get_auth_type(self):
        if self.anonymous:
            return "anonymous"
        else:
            return "jwt"

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
