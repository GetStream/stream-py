from functools import cached_property
import time
from typing import List, Optional
from uuid import uuid4

import jwt
from pydantic_settings import BaseSettings, SettingsConfigDict

from getstream.chat.client import ChatClient
from getstream.chat.async_client import ChatClient as AsyncChatClient
from getstream.common.async_client import CommonClient as AsyncCommonClient
from getstream.common.client import CommonClient
from getstream.feeds.client import FeedsClient
from getstream.models import UserRequest
from getstream.moderation.client import ModerationClient
from getstream.moderation.async_client import ModerationClient as AsyncModerationClient
from getstream.utils import validate_and_clean_url
from getstream.video.client import VideoClient
from getstream.video.async_client import VideoClient as AsyncVideoClient
from typing_extensions import deprecated


BASE_URL = "https://chat.stream-io-api.com/"


class Settings(BaseSettings):
    # Env names: STREAM_API_KEY, STREAM_API_SECRET, STREAM_BASE_URL, STREAM_TIMEOUT
    api_key: str
    api_secret: str
    base_url: Optional[str] = None
    timeout: float = 6.0

    model_config = SettingsConfigDict(
        env_prefix="STREAM_",
    )


class BaseStream:
    def __init__(
        self,
        api_key: Optional[str] = None,
        api_secret: Optional[str] = None,
        timeout: Optional[float] = 6.0,
        base_url: Optional[str] = BASE_URL,
    ):
        if None in (api_key, api_secret, timeout, base_url):
            s = Settings()  # loads from env and optional .env
            api_key = api_key or s.api_key
            api_secret = api_secret or s.api_secret
            base_url = base_url or (s.base_url or BASE_URL)

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


class AsyncStream(BaseStream, AsyncCommonClient):
    """
    A class used to represent a Stream client using async.

    Contains methods to interact with Video and Chat modules of Stream API.
    """

    @cached_property
    def video(self) -> AsyncVideoClient:
        """
        Video stream client.

        """
        return AsyncVideoClient(
            api_key=self.api_key,
            base_url=self.base_url,
            token=self.token,
            timeout=self.timeout,
            stream=self,
        )

    @cached_property
    def chat(self) -> AsyncChatClient:
        """
        Chat stream client.

        """
        return AsyncChatClient(
            api_key=self.api_key,
            base_url=self.base_url,
            token=self.token,
            timeout=self.timeout,
            stream=self,
        )

    @cached_property
    def moderation(self) -> AsyncModerationClient:
        """
        Moderation stream client.

        """
        return AsyncModerationClient(
            api_key=self.api_key,
            base_url=self.base_url,
            token=self.token,
            timeout=self.timeout,
            stream=self,
        )

    @cached_property
    def feeds(self):
        raise NotImplementedError("Feeds not supported for async client")

    async def create_user(self, name: str = "", id: str = str(uuid4()), image=""):
        """
        Creates or updates users. This method performs an "upsert" operation,
        where it checks if each user already exists and updates their information
        if they do, or creates a new user entry if they do not.
        """
        user = UserRequest(name=name, id=id)
        users_map = {user.id: user}
        response = await self.update_users(users_map)
        user = response.data.users[user.id]
        return user

    async def upsert_users(self, *users: UserRequest):
        """
        Creates or updates users. This method performs an "upsert" operation,
        where it checks if each user already exists and updates their information
        if they do, or creates a new user entry if they do not.
        """
        users_map = {u.id: u for u in users}
        return await self.update_users(users_map)


class Stream(BaseStream, CommonClient):
    """
    A class used to represent a Stream client.

    Contains methods to interact with Video and Chat modules of Stream API.
    """

    @classmethod
    @deprecated("from_env is deprecated, use __init__ instead")
    def from_env(cls, timeout: float = 6.0) -> "Stream":
        """
        Construct a StreamClient by loading its credentials and base_url
        from environment variables (via our pydantic Settings).
        """
        settings = Settings()

        return cls(
            api_key=settings.api_key,
            api_secret=settings.api_secret,
            base_url=settings.base_url,
            timeout=timeout,
        )

    def as_async(self) -> "AsyncStream":
        return AsyncStream(
            api_key=self.api_key,
            api_secret=self.api_secret,
            timeout=self.timeout,
            base_url=self.base_url,
        )

    @cached_property
    def video(self) -> VideoClient:
        """
        Video stream client.

        """
        return VideoClient(
            api_key=self.api_key,
            base_url=self.base_url,
            token=self.token,
            timeout=self.timeout,
            stream=self,
        )

    @cached_property
    def chat(self) -> ChatClient:
        """
        Chat stream client.

        """
        return ChatClient(
            api_key=self.api_key,
            base_url=self.base_url,
            token=self.token,
            timeout=self.timeout,
            stream=self,
        )

    @cached_property
    def moderation(self) -> ModerationClient:
        """
        Moderation stream client.

        """
        return ModerationClient(
            api_key=self.api_key,
            base_url=self.base_url,
            token=self.token,
            timeout=self.timeout,
            stream=self,
        )

    @cached_property
    def feeds(self) -> FeedsClient:
        """
        Feeds stream client.

        """
        return FeedsClient(
            api_key=self.api_key,
            base_url=self.base_url,
            token=self.token,
            timeout=self.timeout,
            stream=self,
        )

    def create_user(self, name: str = "", id: str = str(uuid4()), image=""):
        """
        Creates or updates users. This method performs an "upsert" operation,
        where it checks if each user already exists and updates their information
        if they do, or creates a new user entry if they do not.
        """
        user = UserRequest(name=name, id=id)
        users_map = {user.id: user}
        response = self.update_users(users_map)
        user = response.data.users[user.id]
        return user

    def upsert_users(self, *users: UserRequest):
        """
        Creates or updates users. This method performs an "upsert" operation,
        where it checks if each user already exists and updates their information
        if they do, or creates a new user entry if they do not.
        """
        users_map = {u.id: u for u in users}
        return self.update_users(users_map)
