from stream.chat.async_ import ChatClientAsync
from stream.video.async_ import VideoClientAsync


class StreamAsync:
    def __init__(self):
        self.video = VideoClientAsync()
        self.chat = ChatClientAsync()
