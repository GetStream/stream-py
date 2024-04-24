import time
import jwt
from functools import cached_property
from typing import List

from getstream.chat.client import ChatClient
from getstream.common.client import CommonClient
from getstream.utils import validate_and_clean_url
from getstream.video.client import VideoClient

BASE_URL = "https://chat.stream-io-api.com/"


class Stream(CommonClient):
    """
    A class used to represent a Stream client.

    Contains methods to interact with Video and Chat modules of Stream API.
    """

    def __init__(
        self,
        api_key: str,
        api_secret: str,
        timeout=6.0,
        base_url=BASE_URL,
    ):
        if api_key is None or api_key == "":
            raise ValueError("api_key is required")
        if api_secret is None or api_secret == "":
            raise ValueError("api_secret is required")
        self.api_key = api_key
        self.api_secret = api_secret

        if timeout is not None:
            if not isinstance(timeout, (int, float)) or timeout <= 0.0:
                raise ValueError("timeout must be a number greater than zero")
        self.timeout = timeout

        self.base_url = validate_and_clean_url(base_url)
        self.token = self._create_token()
        super().__init__(self.api_key, self.base_url, self.token, self.timeout)

    @cached_property
    def video(self):
        """
        Video stream client.

        """
        return VideoClient(
            api_key=self.api_key,
            base_url=self.base_url,
            token=self.token,
            timeout=self.timeout,
        )

    @cached_property
    def chat(self):
        """
        Chat stream client.

        """
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
        """
            Generates a token for a given user, with an optional expiration time.

            Args:
                user_id (str): The unique identifier of the user for whom the token is being created.
                expiration (int, optional): The duration in seconds after which the token should expire.

            Returns:
                str: A token generated for the user which may include encoded data about the user and
                    the token's expiration time.

        Example:
            >>> client = Stream(api_key="key", api_secret="secret")
            >>> token = client.create_token("alice")  # doctest: +ELLIPSIS

            >>> token = client.create_token("alice", expiration=3600)  # doctest: +ELLIPSIS

            Notes:
                - Expiration is handled as UNIX time (seconds since epoch), and it is recommended to provide this in UTC.
        """

        if user_id is None or user_id == "":
            raise ValueError("user_id is required")

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
