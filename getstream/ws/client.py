from urllib.parse import urlencode

from getstream.utils.event_emitter import StreamAsyncIOEventEmitter
from getstream.version import VERSION

DEFAULT_BASE_URL = "https://chat.stream-io-api.com"


class StreamWS(StreamAsyncIOEventEmitter):
    def __init__(
        self,
        api_key: str,
        api_secret: str,
        user_id: str,
        *,
        base_url: str = DEFAULT_BASE_URL,
        user_agent: str | None = None,
    ):
        super().__init__()
        self.api_key = api_key
        self.api_secret = api_secret
        self.user_id = user_id
        self._base_url = base_url.rstrip("/")
        self._user_agent = user_agent or f"stream-python-client-{VERSION}"
        self._connected = False

    @property
    def ws_url(self) -> str:
        scheme = self._base_url.replace("https://", "wss://").replace(
            "http://", "ws://"
        )
        params = urlencode(
            {
                "api_key": self.api_key,
                "stream-auth-type": "jwt",
                "X-Stream-Client": self._user_agent,
            }
        )
        return f"{scheme}/connect?{params}"

    @property
    def connected(self) -> bool:
        return self._connected
