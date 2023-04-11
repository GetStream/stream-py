import time
import jwt

from stream.chat.chat import Chat

from stream.video.video import Video


class Stream:
    def __init__(self, api_key, api_secret):
        self.api_key = api_key
        self.api_secret = api_secret
        self.base_url = "https://api.example.com"  # Replace with your actual API base URL
        self.video = Video(self)
        self.chat = Chat(self)

    def create_user_token(self, user_id, call_cids=None, role="admin"):
        payload = {
            "sub": user_id,
            "role": role,
            "call_cids": call_cids or [],
            # Set the token expiration time (here, 1 hour)
            "exp": int(time.time()) + 3600,
        }
        token = jwt.encode(payload, self.api_secret, algorithm="HS256")
        return token