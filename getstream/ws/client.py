import asyncio
import json
import logging
import random
import time
from typing import Optional
from urllib.parse import urlencode, urlparse, urlunparse

import jwt
import websockets
from websockets import ClientConnection

from getstream.stream import BASE_URL
from getstream.utils.event_emitter import StreamAsyncIOEventEmitter
from getstream.version import VERSION

logger = logging.getLogger(__name__)


TOKEN_EXPIRED_CODE = 40


class StreamWSAuthError(Exception):
    def __init__(self, message: str, response: dict | None = None):
        super().__init__(message)
        self.response = response or {}


class StreamWS(StreamAsyncIOEventEmitter):
    def __init__(
        self,
        api_key: str,
        api_secret: str,
        user_id: str,
        *,
        base_url: str = BASE_URL,
        user_agent: str | None = None,
        user_details: Optional[dict] = None,
        token: Optional[str] = None,
        healthcheck_interval: float = 25.0,
        healthcheck_timeout: float = 35.0,
        max_retries: int = 5,
        backoff_base: float = 0.25,
        backoff_max: float = 5.0,
    ):
        super().__init__()
        self.api_key = api_key
        self.api_secret = api_secret
        self.user_id = user_id
        self._base_url = base_url.rstrip("/")
        self._user_agent = user_agent or f"stream-python-client-{VERSION}"
        self._user_details = user_details or {"id": user_id}
        self._token = token
        self._static_token = token is not None
        self._healthcheck_interval = healthcheck_interval
        self._healthcheck_timeout = healthcheck_timeout
        self._max_retries = max_retries
        self._backoff_base = backoff_base
        self._backoff_max = backoff_max

        self._websocket: Optional[ClientConnection] = None
        self._connected = False
        self._connection_id: Optional[str] = None
        self._ws_id: int = 0
        self._reader_task: Optional[asyncio.Task] = None
        self._heartbeat_task: Optional[asyncio.Task] = None
        self._last_received: float = 0.0
        self._reconnecting = False
        self._reconnect_task: Optional[asyncio.Task] = None

    @property
    def ws_url(self) -> str:
        parsed = urlparse(self._base_url)
        ws_scheme = "wss" if parsed.scheme == "https" else "ws"
        query = urlencode(
            {
                "api_key": self.api_key,
                "stream-auth-type": "jwt",
                "X-Stream-Client": self._user_agent,
            }
        )
        ws_parsed = parsed._replace(
            scheme=ws_scheme,
            path="/api/v2/connect",
            query=query,
        )
        return urlunparse(ws_parsed)

    @property
    def connected(self) -> bool:
        return self._connected and self._websocket is not None

    @property
    def connection_id(self) -> Optional[str]:
        return self._connection_id

    @property
    def ws_id(self) -> int:
        return self._ws_id

    async def _close_websocket(
        self, code: int = 1000, reason: str = ""
    ) -> None:
        if self._websocket:
            try:
                await self._websocket.close(code=code, reason=reason)
            except Exception:
                logger.debug("Error closing WebSocket", exc_info=True)
            self._websocket = None

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

    async def _open_connection(self) -> dict:
        self._ws_id += 1
        self._websocket = await websockets.connect(
            self.ws_url,
            ping_interval=None,
            ping_timeout=None,
            close_timeout=1.0,
        )

        try:
            auth_payload = {
                "token": self._ensure_token(),
                "user_details": self._user_details,
            }
            await self._websocket.send(json.dumps(auth_payload))

            raw = await self._websocket.recv()
            message = json.loads(raw)

            msg_type = message.get("type")
            if msg_type != "connection.ok":
                raise StreamWSAuthError(
                    f"Expected connection.ok, got {msg_type}: {message}",
                    response=message,
                )
        except Exception:
            await self._close_websocket()
            raise

        self._connection_id = message.get("connection_id")
        self._last_received = time.monotonic()
        return message

    async def __aenter__(self):
        await self.connect()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.disconnect()
        return False

    async def connect(self) -> dict:
        if self._connected:
            raise RuntimeError("Already connected. Call disconnect() first.")

        message = await self._open_connection()
        self._connected = True
        self._start_tasks()
        return message

    def _start_tasks(self) -> None:
        self._reader_task = asyncio.create_task(self._reader_loop())
        self._heartbeat_task = asyncio.create_task(self._heartbeat_loop())

    def _trigger_reconnect(self, reason: str) -> None:
        if self._connected and not self._reconnecting:
            self._reconnecting = True
            self._reconnect_task = asyncio.create_task(self._reconnect(reason))

    async def _reader_loop(self) -> None:
        my_ws_id = self._ws_id
        while self._connected and self._websocket and self._ws_id == my_ws_id:
            try:
                raw = await self._websocket.recv()
                if self._ws_id != my_ws_id:
                    break
                self._last_received = time.monotonic()
                message = json.loads(raw)
                event_type = message.get("type", "unknown")
                try:
                    self.emit(event_type, message)
                except Exception:
                    logger.exception("Error in event listener for %s", event_type)
            except websockets.exceptions.ConnectionClosed as e:
                close_code = getattr(e.rcvd, "code", None) if e.rcvd else None
                logger.debug("WebSocket closed (code=%s) in reader", close_code)
                if close_code == 1000:
                    logger.info("Server closed connection normally, not reconnecting")
                    self._connected = False
                else:
                    self._trigger_reconnect("connection closed")
                break
            except json.JSONDecodeError:
                logger.warning("Failed to parse WebSocket message as JSON")

    async def _heartbeat_loop(self) -> None:
        while self._connected:
            await asyncio.sleep(self._healthcheck_interval)
            if not self._connected or not self._websocket:
                break

            elapsed = time.monotonic() - self._last_received
            if elapsed > self._healthcheck_timeout:
                logger.warning("Healthcheck timeout (%.1fs)", elapsed)
                self._trigger_reconnect("healthcheck timeout")
                break

            try:
                msg = [{"type": "health.check", "client_id": self._connection_id}]
                await self._websocket.send(json.dumps(msg))
                logger.debug("Sent heartbeat")
            except websockets.exceptions.ConnectionClosed:
                logger.debug("WebSocket closed while sending heartbeat")
                self._trigger_reconnect("connection closed")
                break

    async def _reconnect(self, reason: str) -> None:
        logger.info("Reconnecting: %s", reason)

        try:
            await self._cancel_background_tasks()
            await self._close_websocket()

            for attempt in range(1, self._max_retries + 1):
                if not self._connected:
                    return
                delay = min(
                    self._backoff_base * (2 ** (attempt - 1)),
                    self._backoff_max,
                )
                delay *= 1 + random.random()
                logger.debug(
                    "Reconnect attempt %d/%d in %.2fs",
                    attempt,
                    self._max_retries,
                    delay,
                )
                await asyncio.sleep(delay)

                if not self._connected:
                    return

                try:
                    await self._open_connection()
                    self._start_tasks()
                    logger.info("Reconnected after %d attempt(s)", attempt)
                    return
                except StreamWSAuthError as e:
                    error_code = e.response.get("error", {}).get("code")
                    if error_code == TOKEN_EXPIRED_CODE and not self._static_token:
                        logger.info("Token expired (code 40), refreshing")
                        self._token = None
                        continue
                    logger.error("Auth failed during reconnect (code %s)", error_code)
                    self._connected = False
                    return
                except Exception as e:
                    logger.warning("Reconnect attempt %d failed: %s", attempt, e)

            logger.error("All %d reconnect attempts failed", self._max_retries)
            self._connected = False
        finally:
            self._reconnecting = False

    async def _cancel_background_tasks(self) -> None:
        """Cancel reader and heartbeat tasks (safe to call from _reconnect)."""
        for task in (self._reader_task, self._heartbeat_task):
            if task:
                task.cancel()
                try:
                    await task
                except (asyncio.CancelledError, Exception):
                    pass
        self._reader_task = None
        self._heartbeat_task = None

    async def _cancel_all_tasks(self) -> None:
        """Cancel all tasks including reconnect (used by disconnect)."""
        await self._cancel_background_tasks()
        if self._reconnect_task:
            self._reconnect_task.cancel()
            try:
                await self._reconnect_task
            except (asyncio.CancelledError, Exception):
                pass
            self._reconnect_task = None

    async def disconnect(self) -> None:
        self._connected = False
        self._connection_id = None
        await self._cancel_all_tasks()
        await self._close_websocket(code=1000, reason="client disconnect")
