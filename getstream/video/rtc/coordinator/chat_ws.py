"""
WebSocket client for Stream Chat Coordinator.

This module contains the StreamChatWS class that provides an asynchronous WebSocket
client for consuming real-time chat and call events from Stream's Coordinator.
"""

import asyncio
import json
import logging
import random
import time
from typing import List, Optional, Tuple
from urllib.parse import urlparse, urlunparse

import httpx
import jwt
import websockets
from websockets import ClientConnection

from getstream.utils.event_emitter import StreamAsyncIOEventEmitter

from .errors import (
    StreamWSAuthError,
    StreamWSConnectionError,
)

logger = logging.getLogger(__name__)

DEFAULT_WS_URI = "wss://chat.stream-io-api.com/api/v2/connect"

TOKEN_EXPIRED_CODE = 40


class StreamChatWS(StreamAsyncIOEventEmitter):
    """
    Asynchronous WebSocket client for Stream Chat Coordinator.

    This client handles authentication, event dispatching, and connection management
    for consuming real-time events from Stream's Coordinator API.
    """

    def __init__(
        self,
        api_key: str,
        api_secret: str,
        user_id: str,
        user_details: Optional[dict] = None,
        *,
        uri: str = DEFAULT_WS_URI,
        healthcheck_interval: float = 25.0,
        healthcheck_timeout: float = 35.0,
        max_retries: int = 5,
        backoff_base: float = 0.25,
        backoff_factor: float = 2.0,
        backoff_max: float = 5.0,
        logger: Optional[logging.Logger] = None,
        user_token: Optional[str] = None,
        watch_call: Optional[Tuple[str, str]] = None,
        watch_channels: Optional[List[Tuple[str, str]]] = None,
    ):
        super().__init__()

        self.api_key = api_key
        self.api_secret = api_secret
        self.user_id = user_id
        self.user_details = user_details or {"id": user_id}
        self.user_token = user_token
        self.uri = f"{uri}?api_key={api_key}&stream-auth-type=jwt"
        self.healthcheck_interval = healthcheck_interval
        self.healthcheck_timeout = healthcheck_timeout
        self.max_retries = max_retries
        self.backoff_base = backoff_base
        self.backoff_factor = backoff_factor
        self.backoff_max = backoff_max
        self._watch_call = watch_call
        self._watch_channels = watch_channels

        self._logger = logger or globals()["logger"]

        # Connection state
        self._websocket: Optional[ClientConnection] = None
        self._connected = False
        self._client_id: Optional[str] = None
        self._ws_id: int = 0
        self._static_token = user_token is not None

        # Background tasks
        self._reader_task: Optional[asyncio.Task] = None
        self._heartbeat_task: Optional[asyncio.Task] = None
        self._reconnect_task: Optional[asyncio.Task] = None

        # Heartbeat tracking
        self._last_received = 0.0
        self._reconnect_in_progress = False
        self._initial_connection = True

    @property
    def connected(self) -> bool:
        return self._connected and self._websocket is not None

    @property
    def connection_id(self) -> Optional[str]:
        return self._client_id

    @property
    def ws_id(self) -> int:
        return self._ws_id

    async def _build_auth_payload(self) -> dict:
        if not self.user_token:
            self.user_token = jwt.encode(
                {"user_id": self.user_id, "iat": int(time.time()) - 5},
                self.api_secret,
                algorithm="HS256",
            )
        payload = {
            "token": self.user_token,
        }
        if self.user_details:
            payload["user_details"] = self.user_details
        return payload

    async def _open_socket(self) -> dict:
        self._logger.debug("Opening WebSocket connection", extra={"uri": self.uri})

        self._ws_id += 1
        self._websocket = await websockets.connect(
            self.uri,
            ping_interval=None,
            ping_timeout=None,
            close_timeout=1.0,
        )

        try:
            auth_payload = await self._build_auth_payload()
            self._logger.debug("Sending auth payload")
            await self._websocket.send(json.dumps(auth_payload))

            self._logger.debug("Waiting for first server message")
            raw_message = await self._websocket.recv()
            message = json.loads(raw_message)

            msg_type = message.get("type")
            if msg_type != "connection.ok":
                self._logger.error("Authentication failed", extra={"error": message})
                self.emit(msg_type or "error", message)
                raise StreamWSAuthError(
                    f"Expected connection.ok, got {msg_type}: {message}",
                    response=message,
                )
        except Exception:
            if self._websocket:
                try:
                    await self._websocket.close()
                except Exception:
                    pass
                self._websocket = None
            raise

        self._last_received = time.time()
        self._client_id = message.get("connection_id")
        if self._client_id:
            self._logger.debug("Stored client_id", extra={"client_id": self._client_id})

        self._logger.info("Successfully connected and authenticated")
        event_type = message.get("type", "unknown")
        self.emit(event_type, message)

        return message

    async def connect(self) -> dict:
        if self._connected:
            raise RuntimeError("Already connected. Call disconnect() first.")

        self._logger.info("Connecting to coordinator", extra={"uri": self.uri})
        self._initial_connection = True

        try:
            first_message = await self._open_socket()
            self._connected = True
            await self._start_background_tasks()
            self._initial_connection = False
            return first_message

        except StreamWSAuthError:
            raise
        except websockets.exceptions.WebSocketException as e:
            self._logger.error("WebSocket connection failed", exc_info=e)
            raise StreamWSConnectionError(f"WebSocket connection failed: {e}") from e
        except json.JSONDecodeError as e:
            self._logger.error("Failed to parse server message", exc_info=e)
            raise StreamWSConnectionError(f"Invalid JSON from server: {e}") from e
        except Exception as e:
            self._logger.error("Unexpected error during connection", exc_info=e)
            raise StreamWSConnectionError(f"Unexpected connection error: {e}") from e

    async def disconnect(self) -> None:
        self._logger.info("Disconnecting from coordinator")

        self._connected = False
        self._client_id = None
        self._reconnect_in_progress = False
        self._initial_connection = True

        await self._cancel_background_tasks()

        if self._websocket:
            try:
                await self._websocket.close(code=1000, reason="client disconnect")
                self._logger.debug("WebSocket closed cleanly")
            except Exception as e:
                self._logger.warning("Error closing WebSocket", exc_info=e)
            finally:
                self._websocket = None

        self._logger.info("Disconnected from coordinator")

    def _subscription_headers(self) -> dict:
        return {
            "authorization": self.user_token,
            "stream-auth-type": "jwt",
        }

    async def _subscribe_to_call(self, call_type: str, call_id: str) -> None:
        """Subscribe to call events by 'watching' the call with our connection_id."""
        parsed = urlparse(self.uri)
        base_url = urlunparse(parsed._replace(scheme="https", path="", query=""))
        url = f"{base_url}/api/v2/video/call/{call_type}/{call_id}"
        params = {"api_key": self.api_key, "connection_id": self._client_id}
        headers = self._subscription_headers()
        async with httpx.AsyncClient() as http:
            response = await http.post(url, params=params, headers=headers)
            response.raise_for_status()
        self._logger.info(
            "Watching call %s/%s (connection_id=%s)",
            call_type,
            call_id,
            self._client_id,
        )

    async def _subscribe_to_channels(self, channels: List[Tuple[str, str]]) -> None:
        """Subscribe to chat channel events by querying channels with watch=true."""
        parsed = urlparse(self.uri)
        base_url = urlunparse(parsed._replace(scheme="https", path="", query=""))
        url = f"{base_url}/api/v2/chat/channels"
        cids = [f"{ch_type}:{ch_id}" for ch_type, ch_id in channels]
        payload = {
            "filter_conditions": {"cid": {"$in": cids}},
            "watch": True,
            "connection_id": self._client_id,
        }
        headers = self._subscription_headers()
        async with httpx.AsyncClient() as http:
            response = await http.post(
                url,
                params={"api_key": self.api_key},
                headers=headers,
                json=payload,
            )
            response.raise_for_status()
        self._logger.info(
            "Watching %d channel(s) (connection_id=%s)",
            len(channels),
            self._client_id,
        )

    async def _reader_task_func(self) -> None:
        self._logger.debug("Starting reader task")
        my_ws_id = self._ws_id

        try:
            while self._connected and self._websocket and self._ws_id == my_ws_id:
                try:
                    raw_message = await self._websocket.recv()
                    if self._ws_id != my_ws_id:
                        break

                    self._last_received = time.time()

                    try:
                        message = json.loads(raw_message)
                        event_type = message.get("type", "unknown")
                        self._logger.debug(
                            "Received message", extra={"type": event_type}
                        )
                        try:
                            self.emit(event_type, message)
                        except Exception:
                            self._logger.exception(
                                "Error in event listener for %s", event_type
                            )
                    except json.JSONDecodeError as e:
                        self._logger.warning(
                            "Failed to parse message as JSON", exc_info=e
                        )

                except websockets.exceptions.ConnectionClosed as e:
                    close_code = None
                    try:
                        if hasattr(e, "rcvd") and e.rcvd:
                            close_code = getattr(e.rcvd, "code", None)
                    except AttributeError:
                        pass

                    self._logger.debug(
                        "WebSocket closed (code=%s) in reader", close_code
                    )
                    if close_code == 1000:
                        self._logger.info(
                            "Server closed connection normally, not reconnecting"
                        )
                        self._connected = False
                    elif self._connected and not self._reconnect_in_progress:
                        self._trigger_reconnect("connection closed")
                    break
                except websockets.exceptions.WebSocketException as e:
                    self._logger.error(
                        "WebSocket protocol error in reader task", exc_info=e
                    )
                    if self._connected and not self._reconnect_in_progress:
                        self._trigger_reconnect(f"ws exception {e}")
                    break
                except Exception as e:
                    self._logger.error("Unexpected error in reader task", exc_info=e)
                    if self._connected and not self._reconnect_in_progress:
                        self._trigger_reconnect(f"ws read error {e}")
                    break

        except asyncio.CancelledError:
            self._logger.debug("Reader task cancelled")
            raise
        finally:
            self._logger.debug("Reader task ended")

    async def _heartbeat_task_func(self) -> None:
        self._logger.debug("Starting heartbeat task")

        try:
            while self._connected:
                await asyncio.sleep(self.healthcheck_interval)

                if not self._connected:
                    break

                current_time = time.time()

                if current_time - self._last_received > self.healthcheck_timeout:
                    self._logger.warning(
                        "No messages received within timeout period",
                        extra={
                            "last_received": self._last_received,
                            "timeout": self.healthcheck_timeout,
                            "elapsed": current_time - self._last_received,
                        },
                    )
                    if not self._reconnect_in_progress:
                        self._trigger_reconnect("healthcheck timeout")
                    break

                if self._websocket and self._connected:
                    try:
                        heartbeat = [{"type": "health.check"}]
                        if self._client_id:
                            heartbeat[0]["client_id"] = self._client_id
                        await self._websocket.send(json.dumps(heartbeat))
                        self._logger.debug("Sent heartbeat")
                    except websockets.exceptions.ConnectionClosed:
                        self._logger.error(
                            "WebSocket connection closed while sending heartbeat"
                        )
                        if not self._reconnect_in_progress:
                            self._trigger_reconnect("ws connection closed")
                        break
                    except websockets.exceptions.WebSocketException as e:
                        self._logger.error(
                            "WebSocket protocol error while sending heartbeat",
                            exc_info=e,
                        )
                        if not self._reconnect_in_progress:
                            self._trigger_reconnect("heartbeat write error")
                        break
                    except Exception:
                        self._logger.exception(
                            "Unexpected error while sending heartbeat"
                        )
                        if not self._reconnect_in_progress:
                            self._trigger_reconnect("heartbeat unknown error")
                        break

        except asyncio.CancelledError:
            self._logger.debug("Heartbeat task cancelled")
            raise
        finally:
            self._logger.debug("Heartbeat task ended")

    def _trigger_reconnect(self, reason: str) -> None:
        if self._connected and not self._reconnect_in_progress:
            self._reconnect_in_progress = True
            self._reconnect_task = asyncio.create_task(self._reconnect(reason))

    async def _reconnect(self, reason: str = "") -> None:
        self._logger.info("Starting reconnection process: %s", reason)
        self._initial_connection = False

        try:
            await self._cancel_background_tasks()

            if self._websocket:
                try:
                    await self._websocket.close()
                except Exception:
                    pass
                self._websocket = None

            attempt = 0
            for attempt in range(1, self.max_retries + 1):
                if not self._connected:
                    return

                delay = min(
                    self.backoff_base * (self.backoff_factor ** (attempt - 1)),
                    self.backoff_max,
                )
                delay *= 1 + random.random()

                self._logger.info(
                    "Reconnection attempt",
                    extra={
                        "attempt": attempt,
                        "max_retries": self.max_retries,
                        "delay": delay,
                    },
                )
                await asyncio.sleep(delay)

                if not self._connected:
                    return

                try:
                    await self._open_socket()
                    await self._start_background_tasks()
                    self._logger.info("Reconnection successful")
                    return

                except StreamWSAuthError as e:
                    error_code = getattr(e, "response", {}).get("error", {}).get("code")
                    if error_code == TOKEN_EXPIRED_CODE and not self._static_token:
                        self._logger.info("Token expired (code 40), refreshing")
                        self.user_token = None
                        continue
                    self._logger.error(
                        "Auth failed during reconnect (code %s)", error_code
                    )
                    self._connected = False
                    return
                except (OSError, websockets.exceptions.WebSocketException) as e:
                    self._logger.warning(
                        "Reconnection attempt failed",
                        extra={"attempt": attempt, "error": str(e)},
                    )
                    continue
                except Exception as e:
                    self._logger.error(
                        "Unexpected error during reconnection", exc_info=e
                    )
                    continue

            self._logger.error("All reconnection attempts failed")
            self._connected = False
        finally:
            self._reconnect_in_progress = False

    async def _start_background_tasks(self) -> None:
        self._logger.debug("Starting background tasks")
        self._reader_task = asyncio.create_task(self._reader_task_func())
        self._heartbeat_task = asyncio.create_task(self._heartbeat_task_func())

    async def _cancel_background_tasks(self) -> None:
        self._logger.debug("Cancelling background tasks")

        for task in (self._reader_task, self._heartbeat_task, self._reconnect_task):
            if task:
                task.cancel()
                try:
                    await task
                except asyncio.CancelledError:
                    pass
        self._reader_task = None
        self._heartbeat_task = None
        self._reconnect_task = None
