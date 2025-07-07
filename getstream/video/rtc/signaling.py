import asyncio
import threading
import websocket
import logging
import time
from typing import Any, Callable, Awaitable

from getstream.utils import StreamAsyncIOEventEmitter
from .pb.stream.video.sfu.event import events_pb2

logger = logging.getLogger(__name__)


class SignalingError(Exception):
    """Exception raised for errors in the signaling process."""

    pass


class WebSocketClient(StreamAsyncIOEventEmitter):
    """
    WebSocket client for Stream Video signaling.
    Handles WebSocket connection, message serialization/deserialization, and event handling.
    """

    def __init__(
        self,
        url: str,
        join_request: events_pb2.JoinRequest,
        main_loop: asyncio.AbstractEventLoop,
    ):
        """
        Initialize a new WebSocket client.

        Args:
            url: The WebSocket server URL
            join_request: The JoinRequest protobuf message to send for authentication
            main_loop: The main asyncio event loop to run callbacks on
        """
        super().__init__()
        self.url = url
        self.join_request = join_request
        self.main_loop = main_loop
        self.ws = None
        self.first_message_event = threading.Event()
        self.first_message = None
        self.thread = None
        self.running = False
        self.closed = False

        # For ping/health check mechanism
        self.ping_thread = None
        self.last_health_check_time = 0
        self.ping_interval = 10  # seconds

    async def connect(self):
        """
        Establish WebSocket connection and authenticate.

        Returns:
            The first SfuEvent received (JoinResponse if successful)

        Raises:
            SignalingError: If the connection fails or the first message is an error
        """
        if self.closed:
            raise SignalingError("Cannot reconnect a closed WebSocket client")

        self.first_message_event.clear()

        # Create a new WebSocketApp
        self.ws = websocket.WebSocketApp(
            self.url,
            on_open=self._on_open,
            on_message=self._on_message,
            on_error=self._on_error,
            on_close=self._on_close,
        )

        # Start WebSocket in a separate thread
        self.running = True
        self.thread = threading.Thread(target=self._run_websocket, daemon=True)
        self.thread.start()

        # Wait for first message
        await asyncio.get_event_loop().run_in_executor(
            None, self.first_message_event.wait
        )

        # Check if the first message is an error
        if self.first_message and self.first_message.HasField("error"):
            error_msg = self.first_message.error.error.message
            raise SignalingError(f"Connection failed: {error_msg}")

        # Check if we got join_response
        if self.first_message and self.first_message.HasField("join_response"):
            # Start the ping mechanism after successful connection
            self._start_ping_handler()
            return self.first_message

        raise SignalingError("Unexpected first message type")

    def _run_websocket(self):
        """Run the WebSocket connection in the background."""
        self.ws.run_forever()

    def _on_open(self, ws):
        """Handle WebSocket open event."""
        logger.debug("WebSocket connection established")

        # Serialize and send JoinRequest
        request = events_pb2.SfuRequest(join_request=self.join_request)
        ws.send(request.SerializeToString())

    def _on_message(self, ws, message):
        """Handle incoming WebSocket messages."""

        event = events_pb2.SfuEvent()
        event.ParseFromString(message)
        logger.debug(f"WebSocket message received {event.WhichOneof('event_payload')}")

        if event.HasField("health_check_response"):
            logger.debug("received health check response")
            self.last_health_check_time = time.time()

        # If this is the first message, set it and trigger the event
        if not self.first_message_event.is_set():
            self.first_message = event
            self.first_message_event.set()

        # Dispatch to event handlers using emit
        asyncio.run_coroutine_threadsafe(self._dispatch_event(event), self.main_loop)

    def _on_error(self, ws, error):
        """Handle WebSocket error."""
        logger.error(f"WebSocket error: {str(error)}")
        if not self.first_message_event.is_set():
            # Create an error event
            error_event = events_pb2.SfuEvent()
            error_event.error.error.message = str(error)
            self.first_message = error_event
            self.first_message_event.set()

    def _on_close(self, ws, close_status_code, close_msg):
        """Handle WebSocket close event."""
        logger.debug(f"WebSocket connection closed: {close_status_code} {close_msg}")
        self.running = False

    def _start_ping_handler(self):
        """Start the ping mechanism in a background thread."""
        if self.ping_thread is not None:
            return  # Already started

        # Set initial health check time
        self.last_health_check_time = time.time()

        # Start thread for sending pings
        self.ping_thread = threading.Thread(target=self._ping_loop, daemon=True)
        self.ping_thread.start()
        logger.debug("Started ping handler")

    def _ping_loop(self):
        """Run periodic health checks to keep the connection alive."""
        logger.debug("Ping loop started")

        while self.running and not self.closed:
            # Check if we haven't received a health check response in more than twice the ping interval
            current_time = time.time()
            if current_time - self.last_health_check_time > self.ping_interval * 2:
                logger.warning("Health check failed, closing connection")
                self.close()
                return

            # Skip if the connection is closed
            if not self.running or self.closed or self.ws is None:
                return

            try:
                # Create and send health check request
                health_check_req = events_pb2.HealthCheckRequest()
                sfu_request = events_pb2.SfuRequest(
                    health_check_request=health_check_req
                )

                # Send the serialized request
                self.ws.send(sfu_request.SerializeToString())
                logger.debug("Sent health check request")
            except Exception as e:
                logger.error(f"Failed to send health check request: {e}")

            # Sleep for ping interval
            time.sleep(self.ping_interval)

    async def _dispatch_event(self, event):
        """
        Dispatch an event to the appropriate handlers using emit.

        Args:
            event: The SfuEvent to dispatch
        """
        # Get the oneof event type
        event_type = event.WhichOneof("event_payload")
        if event_type:
            payload = getattr(event, event_type)
            # Emit the event using the parent class emit method
            self.emit(event_type, payload)

    def on_event(self, event_type: str, callback: Callable[[Any], Awaitable[None]]):
        """
        Register an event handler for a specific event type.

        Args:
            event_type: The event type to listen for, or "*" for all events
            callback: An async function to call when the event occurs
        """
        # Use the parent class's on method for regular events
        # For wildcard events, use on_wildcard method
        if "*" in event_type:
            self.on_wildcard(event_type, callback)
        else:
            self.on(event_type, callback)

    def close(self):
        """Close the WebSocket connection."""
        if self.closed:
            return

        self.closed = True
        self.running = False

        if self.ws:
            self.ws.close()
            self.ws = None

        if self.thread:
            self.thread.join(timeout=2.0)
            self.thread = None

        if self.ping_thread:
            self.ping_thread.join(timeout=2.0)
            self.ping_thread = None

        # Clear event listeners from parent class
        self.remove_all_listeners()
        self.remove_all_wildcard_listeners()
