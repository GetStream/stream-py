import asyncio
import logging
from typing import AsyncIterator

from getstream.video.call import Call
from getstream.video.rtc.location_discovery import HTTPHintLocationDiscovery

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

    async def __aenter__(self):
        """Async context manager entry that performs location discovery and joins call."""
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

        # Mark as running and clear stop event
        self.running = True
        self._stop_event.clear()

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
        # eventually this will send real events, for now this is just here as placeholder
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

        # Add actual disconnection logic here in the future
        # This would include:
        # 1. Closing WebSocket connections
        # 2. Cleaning up peer connections
        # 3. Potentially sending a leave message to the SFU

        logger.info("Successfully left call")
