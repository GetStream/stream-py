import uuid

import asyncio
import logging
from typing import AsyncIterator

from getstream.video.call import Call
from getstream.video.rtc.location_discovery import HTTPHintLocationDiscovery
from getstream.video.rtc.signaling import WebSocketClient, SignalingError
from getstream.video.rtc.pb.stream.video.sfu.event import events_pb2

# Import join_call_coordinator_request from coordinator module instead of __init__
from getstream.video.rtc.coordinator import join_call_coordinator_request

logger = logging.getLogger("getstream.video.rtc.connection_manager")


class ConnectionError(Exception):
    """Exception raised when connection to the call fails."""

    pass


class ConnectionManager:
    def __init__(self, call: Call, user_id: str = None, create: bool = True, **kwargs):
        self.call = call
        self.user_id = user_id
        self.create = create
        self.kwargs = kwargs
        self.running = False
        self.join_response = None
        self.connection_task = None
        # Add a stop event to signal when to stop iteration
        self._stop_event = asyncio.Event()
        # WebSocket client for SFU communication
        self.ws_client = None
        self.session_id = str(uuid.uuid4())

    async def _full_connect(self):
        """Perform location discovery and join call via coordinator.

        This method handles the full connection process:
        1. Discovering the optimal location
        2. Joining the call via the coordinator API
        3. Establishing WebSocket connection to the SFU

        Raises:
            ConnectionError: If there's an issue joining the call or connecting to the SFU
        """
        # Discover location
        logger.info("Discovering location")
        try:
            discovery = HTTPHintLocationDiscovery(logger=logger)
            location = discovery.discover()
            logger.info(f"Discovered location: {location}")
        except Exception as e:
            logger.error(f"Failed to discover location: {e}")
            # Default to a reasonable location if discovery fails
            location = "FRA"
            logger.info(f"Using default location: {location}")

        # Join call via coordinator
        logger.info("Performing join call request on coordinator API")
        try:
            self.join_response = await join_call_coordinator_request(
                self.call,
                self.user_id,
                create=self.create,
                location=location,
                **self.kwargs,
            )
            logger.info(
                f"Received credentials to connect to SFU {self.join_response.data.credentials.server.url}"
            )
        except Exception as e:
            logger.error(f"Failed to join call: {e}")
            raise ConnectionError(f"Failed to join call: {e}")

        # Connect to SFU via WebSocket
        logger.info("Connecting to SFU via WebSocket")
        try:
            # Create JoinRequest for WebSocket connection
            join_request = self._create_join_request()

            # Get WebSocket URL from the coordinator response
            ws_url = self.join_response.data.credentials.server.ws_endpoint

            # Create WebSocket client
            self.ws_client = WebSocketClient(ws_url, join_request)

            # Connect to the WebSocket server and wait for the first message
            logger.info(f"Establishing WebSocket connection to {ws_url}")
            sfu_event = await self.ws_client.connect()

            logger.info("WebSocket connection established successfully")
            logger.debug(f"Received join response: {sfu_event.join_response}")

        except SignalingError as e:
            logger.error(f"Failed to connect to SFU: {e}")
            # Close the WebSocket if it was created
            if self.ws_client:
                self.ws_client.close()
                self.ws_client = None
            raise ConnectionError(f"Failed to connect to SFU: {e}")
        except Exception as e:
            logger.error(f"Unexpected error connecting to SFU: {e}")
            # Close the WebSocket if it was created
            if self.ws_client:
                self.ws_client.close()
                self.ws_client = None
            raise ConnectionError(f"Unexpected error connecting to SFU: {e}")

        # Mark as running and clear stop event
        self.running = True
        self._stop_event.clear()

    def _create_join_request(self) -> events_pb2.JoinRequest:
        """Create a JoinRequest protobuf message for the WebSocket connection.

        Returns:
            A JoinRequest protobuf message configured with data from the coordinator response
        """
        # Get credentials from the coordinator response
        credentials = self.join_response.data.credentials

        # Create a JoinRequest
        join_request = events_pb2.JoinRequest()
        join_request.token = credentials.token
        join_request.session_id = self.session_id
        return join_request

    async def __aenter__(self):
        """Async context manager entry that performs location discovery and joins call."""
        await self._full_connect()

        # Return self to be used as an async iterator
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit that leaves the call."""
        await self.leave()

    async def __anext__(self):
        """Async iterator implementation to yield events."""
        if not self.running:
            raise StopAsyncIteration

        # Check if stop was requested before waiting
        if self._stop_event.is_set():
            self.running = False
            raise StopAsyncIteration

        # Use wait_for with a short timeout to frequently check self.running
        try:
            # Wait for 100ms, but allow interruption via the stop event
            await asyncio.wait_for(self._stop_event.wait(), 0.1)
            # If we reach here, the event was set
            self.running = False
            raise StopAsyncIteration
        except asyncio.TimeoutError:
            # Timeout means the event wasn't set, so we continue
            return "helloworld"

    def __aiter__(self) -> AsyncIterator:
        """Return self as an async iterator."""
        return self

    async def leave(self):
        """Leave the call and stop yielding events."""
        if not self.running:
            return

        logger.info("Leaving call")
        self.running = False

        # Signal the __anext__ method to stop
        self._stop_event.set()

        # Close the WebSocket connection if it exists
        if self.ws_client:
            logger.info("Closing WebSocket connection")
            self.ws_client.close()
            self.ws_client = None

        logger.info("Successfully left call")
