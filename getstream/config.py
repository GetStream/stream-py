from getstream.version import VERSION


class BaseConfig:
    def __init__(
        self,
        api_key,
        base_url=None,
        token=None,
        headers={},
        anonymous=False,
        timeout=None,
        user_agent=None,
    ):
        self.anonymous = anonymous
        self.timeout = timeout

        self.base_url = base_url
        self.params = {"api_key": api_key}
        self.api_key = api_key
        if token is not None:
            headers["Authorization"] = token
        if user_agent is None:
            user_agent = self._get_user_agent()
        headers["stream-auth-type"] = self._get_auth_type()
        headers["X-Stream-Client"] = user_agent
        self.headers = headers

    def _get_user_agent(self):
        return f"stream-python-client-{VERSION}"

    def _get_auth_type(self):
        if self.anonymous:
            return "anonymous"
        else:
            return "jwt"
