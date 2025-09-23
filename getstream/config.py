from getstream.version import VERSION


class BaseConfig:
    def __init__(
        self,
        api_key,
        base_url=None,
        token=None,
        headers=None,
        anonymous=False,
        timeout=None,
        user_agent=None,
    ):
        self.anonymous = anonymous
        self.timeout = timeout

        self.base_url = base_url
        self.params = {"api_key": api_key}
        self.api_key = api_key

        # Avoid shared mutable defaults and copy any provided headers
        headers_dict = dict(headers) if headers is not None else {}

        if token is not None:
            headers_dict["Authorization"] = token
        if user_agent is None:
            user_agent = self._get_user_agent()
        headers_dict["stream-auth-type"] = self._get_auth_type()
        headers_dict["X-Stream-Client"] = user_agent
        self.headers = headers_dict

    def _get_user_agent(self):
        return f"stream-python-client-{VERSION}"

    def _get_auth_type(self):
        if self.anonymous:
            return "anonymous"
        else:
            return "jwt"
