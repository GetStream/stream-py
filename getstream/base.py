import time
from typing import List

import jwt


class BaseStream:
    def __init__(self, api_key: str, api_secret: str):
        self.api_key = api_key
        self.api_secret = api_secret

    def create_token(
        self,
        user_id: str,
        expiration: int = None,
    ):
        return self._create_token(user_id=user_id, expiration=expiration)

    def create_call_token(
        self,
        user_id: str,
        call_cids: List[str] = None,
        role: str = None,
        expiration: int = None,
    ):
        return self._create_token(
            user_id=user_id, call_cids=call_cids, role=role, expiration=expiration
        )

    def _create_token(
        self,
        user_id: str = None,
        channel_cids: List[str] = None,
        call_cids: List[str] = None,
        role: str = None,
        expiration=None,
    ):
        now = int(time.time())

        claims = {
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

        if expiration is not None:
            claims["exp"] = now + expiration

        token = jwt.encode(claims, self.api_secret, algorithm="HS256")
        return token
