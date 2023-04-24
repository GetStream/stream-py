from stream_sdks import BaseStream
from stream_sdks.chat.sync import ChatClient
from stream_sdks.video.sync import VideoClient


class Stream(BaseStream):
    def __init__(self, api_key: str, api_secret: str, token=None):
        super().__init__(api_key, api_secret)
        if token is None:
            token = self.create_token()
        self.video = VideoClient(
            api_key=api_key,
            base_url="https://video.stream-io-api.com/video",
            token=token,
        )
        self.chat = ChatClient(
            api_key=api_key, base_url="https://chat.stream-io-api.com", token=token
        )
