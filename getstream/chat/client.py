from getstream.chat.rest_client import ChatRestClient


class ChatClient(ChatRestClient):
    def __init__(self, api_key: str, base_url, token, timeout, stream):
        super().__init__(
            api_key=api_key, base_url=base_url, token=token, timeout=timeout
        )
        self.stream = stream
