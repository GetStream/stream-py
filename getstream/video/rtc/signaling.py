import asyncio
import concurrent.futures
import threading
import websocket
import logging
from typing import Any, Callable, Dict, Awaitable, List

from .pb.stream.video.sfu.event import events_pb2

logger = logging.getLogger(__name__)


class SignalingError(Exception):
    """Exception raised for errors in the signaling process."""

    pass


class WebSocketClient:
    """
    WebSocket client for Stream Video signaling.
    Handles WebSocket connection, message serialization/deserialization, and event handling.
    """

    def __init__(self, url: str, join_request: events_pb2.JoinRequest):
        """
        Initialize a new WebSocket client.

        Args:
            url: The WebSocket server URL
            join_request: The JoinRequest protobuf message to send for authentication
        """
        self.url = url
        self.join_request = join_request
        self.ws = None
        self.event_handlers: Dict[str, List[Callable[[Any], Awaitable[None]]]] = {}
        self.first_message_event = asyncio.Event()
        self.first_message = None
        self.thread = None
        self.event_loop = asyncio.new_event_loop()
        self.running = False
        self.closed = False

        # Thread pool for executing callbacks
        self.executor = concurrent.futures.ThreadPoolExecutor(
            max_workers=4, thread_name_prefix="ws-callback-"
        )

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
        await self.first_message_event.wait()

        # Check if the first message is an error
        if self.first_message and self.first_message.HasField("error"):
            error_msg = self.first_message.error.error.description
            raise SignalingError(f"Connection failed: {error_msg}")

        # Check if we got join_response
        if self.first_message and self.first_message.HasField("join_response"):
            return self.first_message

        raise SignalingError("Unexpected first message type")

    def _run_websocket(self):
        """Run the WebSocket connection in the background."""
        asyncio.set_event_loop(self.event_loop)
        self.ws.run_forever()

    def _on_open(self, ws):
        """Handle WebSocket open event."""
        logger.debug("WebSocket connection established")

        # Serialize and send JoinRequest
        request = events_pb2.SfuRequest(join_request=self.join_request)
        ws.send(request.SerializeToString())

    def _on_message(self, ws, message):
        """Handle incoming WebSocket messages."""
        try:
            # Deserialize the message
            event = events_pb2.SfuEvent()
            event.ParseFromString(message)

            # If this is the first message, set it and trigger the event
            if not self.first_message_event.is_set():
                self.first_message = event
                self.event_loop.call_soon_threadsafe(self.first_message_event.set)

            # Dispatch to event handlers
            self._dispatch_event(event)

        except Exception as e:
            logger.error(f"Error handling message: {str(e)}")

    def _on_error(self, ws, error):
        """Handle WebSocket error."""
        logger.error(f"WebSocket error: {str(error)}")
        if not self.first_message_event.is_set():
            # Create an error event
            error_event = events_pb2.SfuEvent()
            error_event.error.error.description = str(error)
            self.first_message = error_event
            self.event_loop.call_soon_threadsafe(self.first_message_event.set)

    def _on_close(self, ws, close_status_code, close_msg):
        """Handle WebSocket close event."""
        logger.debug(f"WebSocket connection closed: {close_status_code} {close_msg}")
        self.running = False

    def _dispatch_event(self, event):
        """
        Dispatch an event to the appropriate handlers.

        Args:
            event: The SfuEvent to dispatch
        """
        # Get the oneof event type
        event_type = event.WhichOneof("event_payload")

        # Run handlers for this specific event type
        if event_type and event_type in self.event_handlers:
            for handler in self.event_handlers[event_type]:
                # Get the specific event payload
                payload = getattr(event, event_type)
                self._run_handler_async(handler, payload)

        # Run wildcard handlers
        if "*" in self.event_handlers:
            for handler in self.event_handlers["*"]:
                self._run_handler_async(handler, event)

    def _run_handler_async(self, handler, payload):
        """
        Run an event handler asynchronously in a separate thread.

        Args:
            handler: The async handler function
            payload: The event payload to pass to the handler
        """

        def run_in_thread():
            # Create a new event loop for this thread
            handler_loop = asyncio.new_event_loop()
            asyncio.set_event_loop(handler_loop)

            # Run the handler in this thread's event loop
            try:
                handler_loop.run_until_complete(handler(payload))
            except Exception as e:
                logger.error(f"Error in event handler: {str(e)}")
            finally:
                handler_loop.close()

        # Submit the handler to the thread pool
        if not self.closed:
            self.executor.submit(run_in_thread)

    def on_event(self, event_type: str, callback: Callable[[Any], Awaitable[None]]):
        """
        Register an event handler for a specific event type.

        Args:
            event_type: The event type to listen for, or "*" for all events
            callback: An async function to call when the event occurs
        """
        if event_type not in self.event_handlers:
            self.event_handlers[event_type] = []

        self.event_handlers[event_type].append(callback)

    def close(self):
        """Close the WebSocket connection and clean up resources."""
        if self.closed:
            return

        self.closed = True
        self.running = False

        # Close the WebSocket connection
        if self.ws:
            self.ws.close()

        # Wait for the thread to finish
        if self.thread and self.thread.is_alive():
            self.thread.join(timeout=1.0)

        # Shutdown the executor
        self.executor.shutdown(wait=False)

        # Clear handlers
        self.event_handlers.clear()

        # Close the event loop
        try:
            # Cancel all running tasks
            for task in asyncio.all_tasks(self.event_loop):
                task.cancel()

            # Run the event loop once to process the cancellations
            self.event_loop.call_soon_threadsafe(self.event_loop.stop)

            # Close the event loop
            if not self.event_loop.is_closed():
                self.event_loop.close()
        except BaseException:
            # Ignore errors during shutdown
            pass
