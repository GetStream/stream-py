from stream.sync.base import BaseClient


class ChatClient(BaseClient):
    def __init__(self, api_key: str, base_url, token: str = None):
        super().__init__(api_key=api_key, base_url=base_url, token=token)