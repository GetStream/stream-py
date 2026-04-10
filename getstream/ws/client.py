import asyncio
import json
import logging
import time
from typing import Optional
from urllib.parse import urlencode

import jwt
import websockets
from websockets import ClientConnection

from getstream.utils.event_emitter import StreamAsyncIOEventEmitter
from getstream.version import VERSION

logger = logging.getLogger(__name__)

DEFAULT_BASE_URL = "https://chat.stream-io-api.com"


class StreamWSAuthError(Exception):
    pass


class StreamWS(StreamAsyncIOEventEmitter):
    def __init__(
        self,
        api_key: str,
        api_secret: str,
        user_id: str,
        *,
        base_url: str = DEFAULT_BASE_URL,
        user_agent: str | None = None,
        user_details: Optional[dict] = None,
        token: Optional[str] = None,
    ):
        super().__init__()
        self.api_key = api_key
        self.api_secret = api_secret
        self.user_id = user_id
        self._base_url = base_url.rstrip("/")
        self._user_agent = user_agent or f"stream-python-client-{VERSION}"
        self._user_details = user_details or {"id": user_id}
        self._token = token

        self._websocket: Optional[ClientConnection] = None
        self._connected = False
        self._connection_id: Optional[str] = None
        self._reader_task: Optional[asyncio.Task] = None

    @property
    def ws_url(self) -> str:
        scheme = self._base_url.replace("https://", "wss://").replace(
            "http://", "ws://"
        )
        params = urlencode(
            {
                "api_key": self.api_key,
                "stream-auth-type": "jwt",
                "X-Stream-Client": self._user_agent,
            }
        )
        return f"{scheme}/connect?{params}"

    @property
    def connected(self) -> bool:
        return self._connected and self._websocket is not None

    @property
    def connection_id(self) -> Optional[str]:
        return self._connection_id

    def _ensure_token(self) -> str:
        if self._token:
            return self._token
        now = int(time.time())
        self._token = jwt.encode(
            {"user_id": self.user_id, "iat": now - 5},
            self.api_secret,
            algorithm="HS256",
        )
        return self._token

    async def connect(self) -> dict:
        if self._connected:
            await self.disconnect()

        self._websocket = await websockets.connect(
            self.ws_url,
            ping_interval=None,
            ping_timeout=None,
            close_timeout=1.0,
        )

        auth_payload = {
            "token": self._ensure_token(),
            "user_details": self._user_details,
        }
        await self._websocket.send(json.dumps(auth_payload))

        raw = await self._websocket.recv()
        message = json.loads(raw)

        if message.get("type") in ("error", "connection.error"):
            await self._websocket.close()
            self._websocket = None
            raise StreamWSAuthError(f"Authentication failed: {message}")

        self._connection_id = message.get("connection_id")
        self._connected = True
        self._reader_task = asyncio.create_task(self._reader_loop())
        return message

    async def _reader_loop(self) -> None:
        while self._connected and self._websocket:
            try:
                raw = await self._websocket.recv()
                message = json.loads(raw)
                event_type = message.get("type", "unknown")
                self.emit(event_type, message)
            except websockets.exceptions.ConnectionClosed:
                logger.debug("WebSocket connection closed in reader")
                break
            except json.JSONDecodeError:
                logger.warning("Failed to parse WebSocket message as JSON")

    async def disconnect(self) -> None:
        self._connected = False
        self._connection_id = None
        if self._reader_task:
            self._reader_task.cancel()
            try:
                await self._reader_task
            except asyncio.CancelledError:
                pass
            self._reader_task = None
        if self._websocket:
            try:
                await self._websocket.close(code=1000, reason="client disconnect")
            except Exception:
                pass
            finally:
                self._websocket = None
