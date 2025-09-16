from getstream.moderation.async_rest_client import ModerationRestClient


class ModerationClient(ModerationRestClient):
    def __init__(self, api_key: str, base_url, token, timeout, stream):
        super().__init__(
            api_key=api_key, base_url=base_url, token=token, timeout=timeout
        )
        self.stream = stream
