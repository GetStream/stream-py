from __future__ import annotations

from contextlib import AsyncExitStack
from functools import cached_property
import time
from typing import List, Optional
from uuid import uuid4

import httpx
import jwt
from pydantic_settings import BaseSettings, SettingsConfigDict

from getstream.common import telemetry
from getstream.chat.client import ChatClient
from getstream.chat.async_client import ChatClient as AsyncChatClient
from getstream.common.async_client import CommonClient as AsyncCommonClient
from getstream.common.client import CommonClient
from getstream.feeds.client import FeedsClient
from getstream.models import FullUserResponse, UserRequest
from getstream.moderation.client import ModerationClient
from getstream.moderation.async_client import ModerationClient as AsyncModerationClient
from getstream.utils import validate_and_clean_url
from getstream.video.client import VideoClient
from getstream.video.async_client import VideoClient as AsyncVideoClient
from typing_extensions import deprecated


BASE_URL = "https://chat.stream-io-api.com/"

# ── Connection pool defaults (CHA-2956) ──────────────────────────────
# DEFAULT_REQUEST_TIMEOUT is the default per-request timeout (was 6.0 prior to 3.5.0).
DEFAULT_REQUEST_TIMEOUT = 30.0
# DEFAULT_MAX_CONNS_PER_HOST caps concurrent TCP connections per host.
DEFAULT_MAX_CONNS_PER_HOST = 5
# DEFAULT_IDLE_TIMEOUT sits below the typical 60s LB idle timeout with a 5s safety margin.
DEFAULT_IDLE_TIMEOUT = 55.0
# DEFAULT_CONNECT_TIMEOUT caps TCP + TLS handshake duration.
DEFAULT_CONNECT_TIMEOUT = 10.0


class Settings(BaseSettings):
    # Env names: STREAM_API_KEY, STREAM_API_SECRET, STREAM_BASE_URL, STREAM_TIMEOUT, STREAM_REQUEST_TIMEOUT, STREAM_MAX_CONNS_PER_HOST, STREAM_IDLE_TIMEOUT, STREAM_CONNECT_TIMEOUT
    api_key: str
    api_secret: Optional[str] = None
    base_url: Optional[str] = None
    # `timeout` kept as alias for `request_timeout` for backward compat.
    timeout: float = DEFAULT_REQUEST_TIMEOUT
    request_timeout: Optional[float] = None
    max_conns_per_host: int = DEFAULT_MAX_CONNS_PER_HOST
    idle_timeout: float = DEFAULT_IDLE_TIMEOUT
    connect_timeout: float = DEFAULT_CONNECT_TIMEOUT

    model_config = SettingsConfigDict(
        env_prefix="STREAM_",
    )


class BaseStream:
    def __init__(
        self,
        api_key: Optional[str] = None,
        api_secret: Optional[str] = None,
        timeout: Optional[float] = None,
        base_url: Optional[str] = BASE_URL,
        user_agent: Optional[str] = None,
        transport=None,
        http_client=None,
        token: Optional[str] = None,
        request_timeout: Optional[float] = None,
        max_conns_per_host: Optional[int] = None,
        idle_timeout: Optional[float] = None,
        connect_timeout: Optional[float] = None,
    ):
        """Build a Stream client.

        Pass exactly one of ``api_secret`` or ``token``:
        - ``api_secret`` enables a server-side client that can mint user tokens and call protected admin endpoints.
        - ``token`` enables a client-side client authenticated as a single user. Token-only clients cannot mint tokens or call admin endpoints.

        Any of ``api_key``, ``api_secret``, ``base_url`` left as ``None`` are loaded from ``STREAM_*`` env vars; passing ``token`` skips the ``api_secret`` env fallback.

        Args:
            api_key: Project API key. Falls back to ``STREAM_API_KEY``.
            api_secret: Project API secret. Mutually exclusive with ``token``. Falls back to ``STREAM_API_SECRET`` only when ``token`` is also ``None``.
            timeout: HTTP request timeout in seconds; must be > 0. Kept as a backward-compat alias for ``request_timeout``.
            base_url: API base URL. Falls back to ``STREAM_BASE_URL`` then to the SDK default.
            user_agent: Optional custom ``User-Agent`` string.
            transport: Optional ``httpx`` transport. Mutually exclusive with ``http_client``.
            http_client: Optional pre-built ``httpx`` client. Mutually exclusive with ``transport``. When provided, sub-clients (video/chat/moderation) reuse it instead of opening their own.
            token: Pre-minted user JWT. Mutually exclusive with ``api_secret``.
            request_timeout: Default per-request timeout in seconds. Default 30.0. Replaces the older ``timeout`` kwarg; ``timeout`` is kept as an alias for backward compatibility.
            max_conns_per_host: Max concurrent TCP connections per host. Default 5. Ignored when ``http_client`` is set.
            idle_timeout: Idle connection lifetime in seconds. Default 55.0 (sits 5s under the typical 60s LB idle timeout). Ignored when ``http_client`` is set.
            connect_timeout: TCP + TLS handshake timeout in seconds. Default 10.0. Ignored when ``http_client`` is set.

        Raises:
            ValueError: If both ``transport`` and ``http_client`` are set; if neither ``api_secret`` nor ``token`` can be resolved; if both are provided; if either is the empty string; if ``api_key`` is missing; or if ``request_timeout`` is not a positive number.
        """
        if transport is not None and http_client is not None:
            raise ValueError("Cannot specify both 'transport' and 'http_client'")

        # Env fallback for anything not explicitly provided. A caller-supplied
        # token short-circuits api_secret loading so token-only callers don't
        # need STREAM_API_SECRET in env.
        if (
            api_key is None
            or base_url is None
            or (api_secret is None and token is None)
        ):
            s = Settings()
            api_key = api_key or s.api_key
            base_url = base_url or (s.base_url or BASE_URL)
            if token is None and api_secret is None:
                api_secret = s.api_secret

        # Env fallback + defaults for the 4 pool knobs and request_timeout. `timeout` is a backward-compat alias for `request_timeout`.
        s_for_pool: Optional[Settings] = None

        def _settings() -> Settings:
            nonlocal s_for_pool
            if s_for_pool is None:
                s_for_pool = Settings()
            return s_for_pool

        # request_timeout precedence: explicit kwarg > explicit timeout kwarg > STREAM_REQUEST_TIMEOUT > STREAM_TIMEOUT > DEFAULT_REQUEST_TIMEOUT.
        if request_timeout is None:
            if timeout is not None:
                request_timeout = timeout
            else:
                s = _settings()
                request_timeout = (
                    s.request_timeout if s.request_timeout is not None else s.timeout
                )

        if max_conns_per_host is None:
            max_conns_per_host = _settings().max_conns_per_host
        if idle_timeout is None:
            idle_timeout = _settings().idle_timeout
        if connect_timeout is None:
            connect_timeout = _settings().connect_timeout

        if not api_key:
            raise ValueError("api_key is required")
        if api_secret and token:
            raise ValueError("Pass either api_secret or token, not both")
        if api_secret == "" or token == "":
            raise ValueError("api_secret and token must not be empty strings")
        if api_secret is None and token is None:
            raise ValueError("Either api_secret or token is required")

        self.api_key = api_key
        self._api_secret = api_secret or None

        if not isinstance(request_timeout, (int, float)) or request_timeout <= 0.0:
            raise ValueError("request_timeout must be a number greater than zero")
        self.timeout = request_timeout
        self.request_timeout = request_timeout
        self.max_conns_per_host = max_conns_per_host
        self.idle_timeout = idle_timeout
        self.connect_timeout = connect_timeout

        self.base_url = validate_and_clean_url(base_url)
        self.user_agent = user_agent
        self._transport = transport
        self._http_client = http_client
        self.token = token or self._create_token()
        # Pool knobs are read by BaseClient via getattr(self, ...) since the intermediate generated REST clients (CommonRestClient etc.) do not forward these kwargs. self.max_conns_per_host / idle_timeout / connect_timeout were set above before super().__init__().
        super().__init__(
            self.api_key, self.base_url, self.token, self.timeout, self.user_agent
        )
        # After super().__init__(), self.client is fully built and configured.
        # When the user provided custom HTTP config, sub-clients share this
        # client instead of each building their own.
        if transport is not None or http_client is not None:
            self._shared_client = self.client
        else:
            self._shared_client = None

    @property
    def api_secret(self) -> str:
        """
        Get api secret if it's set.
        Otherwise, raise a ValueError.
        """
        if self._api_secret is None:
            raise ValueError(
                "api_secret is required; this client was initialized with a token"
            )
        return self._api_secret

    @property
    def has_api_secret(self) -> bool:
        """
        Check if api secret is set for this client.
        """
        return self._api_secret is not None

    def _apply_shared_client(self, sub_client):
        """Replace a sub-client's auto-created httpx client with the shared
        one built from user-provided transport/http_client config."""
        if self._shared_client is not None:
            if isinstance(sub_client.client, httpx.Client):
                sub_client.client.close()
            sub_client.client = self._shared_client
            sub_client._owns_http_client = False
        return sub_client

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

        return self._create_token(
            user_id=user_id, expiration=expiration, iat=int(time.time()) - 5
        )

    def clone_for_token(self, token: str):
        """Return a sibling client authenticated with the given user token.

        Keeps this client's ``api_key`` and ``base_url``. The clone is
        token-only; it cannot mint further tokens.
        """
        return self.__class__(
            api_key=self.api_key,
            token=token,
            base_url=self.base_url,
            timeout=self.timeout,
            user_agent=self.user_agent,
        )

    def create_call_token(
        self,
        user_id: str,
        call_cids: List[str] = None,
        role: str = None,
        expiration: int = None,
    ):
        return self._create_token(
            user_id=user_id,
            call_cids=call_cids,
            role=role,
            expiration=expiration,
            iat=int(time.time() - 5),
        )

    def _create_token(
        self,
        user_id: str = None,
        channel_cids: List[str] = None,
        call_cids: List[str] = None,
        role: str = None,
        expiration=None,
        iat: int = None,
    ):
        now = int(time.time())

        claims = {}

        if iat is not None:
            claims["iat"] = iat

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
        return self._apply_shared_client(
            AsyncVideoClient(
                api_key=self.api_key,
                base_url=self.base_url,
                token=self.token,
                timeout=self.timeout,
                stream=self,
                user_agent=self.user_agent,
            )
        )

    @cached_property
    def chat(self) -> AsyncChatClient:
        """
        Chat stream client.

        """
        return self._apply_shared_client(
            AsyncChatClient(
                api_key=self.api_key,
                base_url=self.base_url,
                token=self.token,
                timeout=self.timeout,
                stream=self,
                user_agent=self.user_agent,
            )
        )

    @cached_property
    def moderation(self) -> AsyncModerationClient:
        """
        Moderation stream client.

        """
        return self._apply_shared_client(
            AsyncModerationClient(
                api_key=self.api_key,
                base_url=self.base_url,
                token=self.token,
                timeout=self.timeout,
                stream=self,
                user_agent=self.user_agent,
            )
        )

    async def aclose(self):
        """Close all child clients and the main HTTPX client."""
        # AsyncExitStack ensures all clients are closed even if one fails.
        # video/chat/moderation are @cached_property - only close if accessed.
        async with AsyncExitStack() as stack:
            cached = self.__dict__
            if "video" in cached:
                stack.push_async_callback(self.video.aclose)
            if "chat" in cached:
                stack.push_async_callback(self.chat.aclose)
            if "moderation" in cached:
                stack.push_async_callback(self.moderation.aclose)
            stack.push_async_callback(super().aclose)

    @cached_property
    def feeds(self):
        raise NotImplementedError("Feeds not supported for async client")

    @telemetry.operation_name("getstream.api.common.create_user")
    async def create_user(
        self, name: str = "", id: str = "", image: str = ""
    ) -> FullUserResponse:
        """
        Creates or updates users. This method performs an "upsert" operation,
        where it checks if each user already exists and updates their information
        if they do, or creates a new user entry if they do not.
        """
        id = id or str(uuid4())
        user = UserRequest(name=name, id=id, image=image)
        users_map = {user.id: user}
        response = await self.update_users(users_map)
        user = response.data.users[user.id]
        return user

    @telemetry.operation_name("getstream.api.common.upsert_users")
    async def upsert_users(self, *users: UserRequest):
        """
        Creates or updates users. This method performs an "upsert" operation,
        where it checks if each user already exists and updates their information
        if they do, or creates a new user entry if they do not.
        """
        users_map = {u.id: u for u in users}
        return await self.update_users(users_map)

    def verify_signature(self, body, signature):
        """Verify a webhook signature using this client's API secret.

        Convenience wrapper around getstream.webhook.verify_signature that
        supplies the secret automatically. The module-level function remains
        available for callers who want explicit control.
        """
        from .webhook import verify_signature as _verify_signature

        return _verify_signature(body, signature, self.api_secret)

    def verify_and_parse_webhook(self, body, signature):
        """Verify and parse a webhook payload in one call, using this client's
        API secret.

        Handles gzip-compressed bodies transparently via magic-byte detection.
        Raises getstream.webhook.InvalidWebhookError on signature mismatch or
        parse failures.

        Note: this is intentionally a synchronous ``def`` rather than ``async
        def`` because it performs no I/O; it's CPU-bound (HMAC + gzip + JSON
        parsing).
        """
        from .webhook import verify_and_parse_webhook as _verify_and_parse_webhook

        return _verify_and_parse_webhook(body, signature, self.api_secret)

    def parse_sqs(self, message_body):
        """Decode + parse a Stream-delivered SQS message body.

        Convenience wrapper around getstream.webhook.parse_sqs. No signature is
        required; SQS deliveries are authenticated via AWS IAM.
        """
        from .webhook import parse_sqs as _parse_sqs

        return _parse_sqs(message_body)

    def parse_sns(self, notification_body):
        """Decode + parse a Stream-delivered SNS notification body.

        Accepts either the raw SNS HTTP envelope JSON or the pre-extracted Message
        string. Convenience wrapper around getstream.webhook.parse_sns. No signature
        is required; SNS deliveries are authenticated via AWS IAM.
        """
        from .webhook import parse_sns as _parse_sns

        return _parse_sns(notification_body)


class Stream(BaseStream, CommonClient):
    """
    A class used to represent a Stream client.

    Contains methods to interact with Video and Chat modules of Stream API.
    """

    @classmethod
    @deprecated("from_env is deprecated, use __init__ instead")
    def from_env(cls, timeout: float = 6.0) -> Stream:
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
            api_secret=self._api_secret,
            token=None if self.has_api_secret else self.token,
            timeout=self.timeout,
            base_url=self.base_url,
            user_agent=self.user_agent,
        )

    @cached_property
    def video(self) -> VideoClient:
        """
        Video stream client.

        """
        return self._apply_shared_client(
            VideoClient(
                api_key=self.api_key,
                base_url=self.base_url,
                token=self.token,
                timeout=self.timeout,
                stream=self,
                user_agent=self.user_agent,
            )
        )

    @cached_property
    def chat(self) -> ChatClient:
        """
        Chat stream client.

        """
        return self._apply_shared_client(
            ChatClient(
                api_key=self.api_key,
                base_url=self.base_url,
                token=self.token,
                timeout=self.timeout,
                stream=self,
                user_agent=self.user_agent,
            )
        )

    @cached_property
    def moderation(self) -> ModerationClient:
        """
        Moderation stream client.

        """
        return self._apply_shared_client(
            ModerationClient(
                api_key=self.api_key,
                base_url=self.base_url,
                token=self.token,
                timeout=self.timeout,
                stream=self,
                user_agent=self.user_agent,
            )
        )

    @cached_property
    def feeds(self) -> FeedsClient:
        """
        Feeds stream client.

        """
        return self._apply_shared_client(
            FeedsClient(
                api_key=self.api_key,
                base_url=self.base_url,
                token=self.token,
                timeout=self.timeout,
                stream=self,
                user_agent=self.user_agent,
            )
        )

    @telemetry.operation_name("getstream.api.common.create_user")
    def create_user(
        self, name: str = "", id: str = "", image: str = ""
    ) -> FullUserResponse:
        """
        Creates or updates users. This method performs an "upsert" operation,
        where it checks if each user already exists and updates their information
        if they do, or creates a new user entry if they do not.
        """
        id = id or str(uuid4())
        user = UserRequest(name=name, id=id, image=image)
        users_map = {user.id: user}
        response = self.update_users(users_map)
        user = response.data.users[user.id]
        return user

    @telemetry.operation_name("getstream.api.common.upsert_users")
    def upsert_users(self, *users: UserRequest):
        """
        Creates or updates users. This method performs an "upsert" operation,
        where it checks if each user already exists and updates their information
        if they do, or creates a new user entry if they do not.
        """
        users_map = {u.id: u for u in users}
        return self.update_users(users_map)

    def verify_signature(self, body, signature):
        """Verify a webhook signature using this client's API secret.

        Convenience wrapper around getstream.webhook.verify_signature that
        supplies the secret automatically. The module-level function remains
        available for callers who want explicit control.
        """
        from .webhook import verify_signature as _verify_signature

        return _verify_signature(body, signature, self.api_secret)

    def verify_and_parse_webhook(self, body, signature):
        """Verify and parse a webhook payload in one call, using this client's
        API secret.

        Handles gzip-compressed bodies transparently via magic-byte detection.
        Raises getstream.webhook.InvalidWebhookError on signature mismatch or
        parse failures.
        """
        from .webhook import verify_and_parse_webhook as _verify_and_parse_webhook

        return _verify_and_parse_webhook(body, signature, self.api_secret)

    def parse_sqs(self, message_body):
        """Decode + parse a Stream-delivered SQS message body.

        Convenience wrapper around getstream.webhook.parse_sqs. No signature is
        required; SQS deliveries are authenticated via AWS IAM.
        """
        from .webhook import parse_sqs as _parse_sqs

        return _parse_sqs(message_body)

    def parse_sns(self, notification_body):
        """Decode + parse a Stream-delivered SNS notification body.

        Accepts either the raw SNS HTTP envelope JSON or the pre-extracted Message
        string. Convenience wrapper around getstream.webhook.parse_sns. No signature
        is required; SNS deliveries are authenticated via AWS IAM.
        """
        from .webhook import parse_sns as _parse_sns

        return _parse_sns(notification_body)
