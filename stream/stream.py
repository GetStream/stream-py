import time
import httpx
import jwt

from stream.chat.chat import Chat

from stream.video.video import Video

from stream.version import VERSION

class Stream:
    def __init__(self, api_key, api_secret):
        self.api_key = api_key
        self.api_secret = api_secret
        self.video = Video(self)
        self.chat = Chat(self)
        # admin token
        self.admin_token = self.create_user_token("admin-user")


    def create_user_token(self, user_id, expiration=None):#call_cids=None 
        now = int(time.time())
        
        claims = {
            "iss": f"stream-video-python@{VERSION}",  # Replace with your library version
            "sub": f"user/{user_id}",
            "iat": now,
        }

        if expiration is not None:
            claims["exp"] = now + int(expiration.total_seconds())
        
        token = jwt.encode(claims, self.api_secret, algorithm="HS256")
        return token


    