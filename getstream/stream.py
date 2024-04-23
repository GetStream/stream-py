import time
import jwt
from functools import cached_property
from typing import List

from getstream.chat import ChatClient
from getstream.common import CommonClient
from getstream.video import VideoClient


class Stream(CommonClient):
    """
    A class used to represent a Stream client.

    Contains methods to interact with Video and Chat modules of Stream API.
    """

    BASE_URL = "https://stream-io-api.com"

    def __init__(
        self,
        api_key: str,
        api_secret: str,
        timeout=None,
        base_url=None,
    ):
        if api_key is None:
            raise ValueError("api_key is required")
        if api_secret is None:
            raise ValueError("api_secret is required")
        self.api_key = api_key
        self.api_secret = api_secret
        self.timeout = timeout
        self.base_url = base_url or self.BASE_URL
        self.token = self._create_token()
        super().__init__(self.api_key, self.base_url, self.token, self.timeout)

    @cached_property
    def video(self):
        return VideoClient(
            api_key=self.api_key,
            base_url=self.base_url,
            token=self.token,
            timeout=self.timeout,
        )

    @cached_property
    def chat(self):
        return ChatClient(
            api_key=self.api_key,
            base_url=self.base_url,
            token=self.token,
            timeout=self.timeout,
        )

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
