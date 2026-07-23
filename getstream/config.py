from dataclasses import dataclass

from getstream.version import VERSION


@dataclass(frozen=True)
class RetryConfig:
    """Opt-in auto-retry policy. Disabled by default: the client performs
    exactly one attempt and surfaces errors unchanged. When enabled, only
    GET/HEAD requests failing with HTTP 429 or a transport error are retried,
    and never when the backend marked the error unrecoverable."""

    enabled: bool = False
    max_attempts: int = 3
    max_backoff: float = 30.0

    def __post_init__(self):
        if self.max_attempts < 1:
            raise ValueError("max_attempts must be >= 1")
        if self.max_backoff < 0:
            raise ValueError("max_backoff must be >= 0")


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
        max_conns_per_host=None,
        idle_timeout=None,
        connect_timeout=None,
    ):
        self.anonymous = anonymous
        self.timeout = timeout
        self.max_conns_per_host = max_conns_per_host
        self.idle_timeout = idle_timeout
        self.connect_timeout = connect_timeout

        self.base_url = base_url
        self.params = {"api_key": api_key}
        self.api_key = api_key
        self.token = token

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
