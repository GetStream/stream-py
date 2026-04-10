from getstream.utils.event_emitter import StreamAsyncIOEventEmitter


class StreamWS(StreamAsyncIOEventEmitter):
    def __init__(
        self,
        api_key: str,
        api_secret: str,
        user_id: str,
    ):
        super().__init__()
        self.api_key = api_key
        self.api_secret = api_secret
        self.user_id = user_id
        self._connected = False

    @property
    def connected(self) -> bool:
        return self._connected
