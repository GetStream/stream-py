import time

import jwt

from stream.version import VERSION


class BaseStream:
    def __init__(self, api_key: str, api_secret: str):
        self.api_key = api_key
        self.api_secret = api_secret

    def create_token(
        self, user_id, channel_cids=None, call_cids=None, role=None, expiration=None
    ):
        now = int(time.time())

        claims = {
            "iss": f"stream-video-python@{VERSION}",  # Replace with your library version
            "sub": f"user/{user_id}",
            "iat": now,
            "user_id": user_id,
        }

        if channel_cids is not None:
            claims["channel_cids"] = channel_cids

        if call_cids is not None:
            claims["call_cids"] = call_cids

        if role is not None:
            claims["role"] = role

        if expiration is not None:
            claims["exp"] = now + int(expiration.total_seconds())

        token = jwt.encode(claims, self.api_secret, algorithm="HS256")
        return token
