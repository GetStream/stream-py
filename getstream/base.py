import time
from typing import List

import jwt

from getstream.version import VERSION


class BaseStream:
    def __init__(self, api_key: str, api_secret: str):
        self.api_key = api_key
        self.api_secret = api_secret

    def create_token(
        self,
        user_id: str = None,
        channel_cids: List[str] = None,
        call_cids: List[str] = None,
        role: str = None,
        expiration=None,
    ):
        now = int(time.time())

        claims = {
            "iss": f"stream-video-python@{VERSION}",  # Replace with your library versio
            "iat": now,
        }

        if channel_cids is not None:
            claims["channel_cids"] = channel_cids

        if call_cids is not None:
            claims["call_cids"] = call_cids

        if role is not None:
            claims["role"] = role

        if user_id is not None:
            claims["user_id"] = user_id
            claims["sub"] = f"user/{user_id}"
        else:
            claims["sub"] = "server-side"

        if expiration is not None:
            claims["exp"] = now + int(expiration.total_seconds())

        token = jwt.encode(claims, self.api_secret, algorithm="HS256")
        return token
