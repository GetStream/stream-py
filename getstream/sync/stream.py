from getstream import BaseStream
from getstream.chat.sync import ChatClient
from getstream.video import VideoClient


class Stream(BaseStream):
    def __init__(self, api_key: str, api_secret: str, token=None,timeout=None,user_agent=None,video_base_url=None):
        super().__init__(api_key, api_secret)
        if token is None:
            token = self.create_token()
        if video_base_url is None:
            video_base_url = "https://video.stream-io-api.com/video"
        self.video = VideoClient(
            api_key=api_key,
            base_url=video_base_url,
            token=token,
            timeout=timeout,
            user_agent=user_agent
        )
        self.chat = ChatClient(
            api_key=api_key, base_url="https://chat.stream-io-api.com", token=token
        )
