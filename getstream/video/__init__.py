from __future__ import annotations
from typing import TYPE_CHECKING

import re
import time
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Optional, Dict, Union

import jwt

from getstream.models import CallResponse

if TYPE_CHECKING:
    from getstream.video.client import VideoClient
    from getstream.video.async_client import VideoClient as AsyncVideoClient


# Default lifetime of the token in an SRT address: 24 hours.
DEFAULT_SRT_TOKEN_EXPIRATION_SECONDS = 24 * 60 * 60

# SRT caps the stream id at 512 bytes; encoders refuse a longer one.
MAX_SRT_STREAM_ID_BYTES = 512


@dataclass
class SRTCredentials:
    """SRT address for an encoder (OBS, ffmpeg, ...) to publish into a call.

    ``address`` contains a user token, so it is left out of ``repr()`` and
    ``str()``. Read the attribute directly when you need it.
    """

    address: str
    expires_at: Optional[datetime] = None

    def __repr__(self) -> str:
        return f"SRTCredentials(address='[redacted]', expires_at={self.expires_at!r})"

    __str__ = __repr__


class BaseCall:
    def __init__(
        self,
        client: Union[VideoClient | AsyncVideoClient],
        call_type: str,
        call_id: Optional[str] = None,
        custom_data: Optional[Dict] = None,
    ):
        self.id = call_id
        self.call_type = call_type
        self.client = client
        self.custom_data = custom_data or {}
        self._data: Optional[CallResponse] = None

    def _sync_from_response(self, data):
        if hasattr(data, "call") and isinstance(data.call, CallResponse):
            self.custom_data = data.call.custom
            self._data = data.call

    def connect_openai(
        self, openai_api_key, agent_user_id, model="gpt-4o-realtime-preview"
    ):
        from .openai import get_openai_realtime_client, ConnectionManagerWrapper

        client = get_openai_realtime_client(openai_api_key, self.client.base_url or "")
        token = self.client.stream.create_token(agent_user_id)
        connection_manager = client.beta.realtime.connect(
            extra_query={
                "call_type": self.call_type,
                "call_id": self.id,
                "api_key": self.client.api_key,
            },
            model=model,
            extra_headers={
                "Authorization": f"Bearer {openai_api_key}",
                "OpenAI-Beta": "realtime=v1",
                "Stream-Authorization": token,
            },
        )

        # Wrap the connection manager to check for errors in the first message
        return ConnectionManagerWrapper(connection_manager, self.call_type, self.id)

    def create_srt_credentials(
        self, user_id: str, expiration: Optional[int] = None
    ) -> SRTCredentials:
        """Create the SRT address an encoder uses to publish into this call.

        The address embeds a user token that can only join this call and
        expires after ``expiration`` seconds (24 hours by default). The token
        is checked again whenever the stream reconnects, and at least every
        6 hours during a stream, so it must stay valid until the stream ends.
        Treat the address as a secret.

        Args:
            user_id: the user the encoder publishes as.
            expiration: how long the address works, in seconds. Defaults to
                24 hours.
        """
        if self._data is None:
            raise TypeError(
                "call object is not initialized, make sure to call .get or .get_or_create first"
            )

        if expiration is None:
            expiration = DEFAULT_SRT_TOKEN_EXPIRATION_SECONDS
        if isinstance(expiration, bool) or not isinstance(expiration, int):
            raise TypeError("expiration must be an int number of seconds")
        if expiration <= 0:
            raise ValueError("expiration must be a positive number of seconds")
        if not user_id:
            raise ValueError("user_id is required")

        now = int(time.time())
        token = self.client.stream._create_token(
            user_id=user_id,
            iat=now - 5,
            expiration=expiration,
            scoped_call_cid=f"{self.call_type}:{self.id}",
        )
        passphrase = token.split(".")[2]
        address = self._data.ingress.srt.address.replace(
            "{passphrase}", passphrase
        ).replace("{token}", token)

        stream_id = re.search(r"[?&]streamid=([^&]*)", address)
        if stream_id is not None:
            size = len(stream_id.group(1).encode("utf-8"))
            if size > MAX_SRT_STREAM_ID_BYTES:
                raise ValueError(
                    f"the SRT stream id is {size} bytes, over the "
                    f"{MAX_SRT_STREAM_ID_BYTES}-byte SRT limit; use a shorter "
                    "user ID or call ID"
                )

        exp = jwt.decode(token, options={"verify_signature": False})["exp"]
        return SRTCredentials(
            address=address,
            expires_at=datetime.fromtimestamp(exp, tz=timezone.utc),
        )
