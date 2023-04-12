from stream import BaseStream
from stream.chat.sync import ChatClient
from stream.video.sync import VideoClient


class Stream(BaseStream):
    def __init__(self, api_key: str, api_secret: str):
        super().__init__(api_key, api_secret)
        token = self.create_token("admin-user")
        self.video = VideoClient(
            api_key=api_key,
            base_url="https://video.stream-io-api.com/video",
            token=token,
        )
        self.chat = ChatClient(
            api_key=api_key, base_url="https://chat.stream-io-api.com", token=token
        )
