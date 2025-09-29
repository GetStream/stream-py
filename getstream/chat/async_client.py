from getstream.chat.async_channel import Channel
from getstream.chat.async_rest_client import ChatRestClient


class ChatClient(ChatRestClient):
    def __init__(self, api_key: str, base_url, token, timeout, stream, user_agent=None):
        super().__init__(
            api_key=api_key,
            base_url=base_url,
            token=token,
            timeout=timeout,
            user_agent=user_agent,
        )
        self.stream = stream

    def channel(self, call_type: str, id: str) -> Channel:
        return Channel(self, call_type, id)
