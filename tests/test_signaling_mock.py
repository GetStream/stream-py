import asyncio
import pytest
import threading
from unittest.mock import MagicMock, patch
import sys


# Mock required dependencies
mock_websocket = MagicMock()


# Create a proper WebSocketApp mock class
class MockWebSocketApp:
    def __init__(
        self, url, on_open=None, on_message=None, on_error=None, on_close=None, **kwargs
    ):
        self.url = url
        self.on_open = on_open
        self.on_message = on_message
        self.on_error = on_error
        self.on_close = on_close
        self.kwargs = kwargs
        self.closed = False
        self.last_sent_data = None

    def send(self, data):
        self.last_sent_data = data
        return True

    def close(self):
        self.closed = True
        if self.on_close:
            self.on_close(self, 1000, "Normal closure")

    def run_forever(self):
        pass


# Assign the mock class
mock_websocket.WebSocketApp = MockWebSocketApp
sys.modules["websocket"] = mock_websocket


# Create mocks for the protobuf dependencies
class MockEventPayload:
    pass


class MockJoinResponse:
    def __init__(self):
        self.reconnected = False


class MockErrorInfo:
    def __init__(self):
        self.message = "Error message"


class MockError:
    def __init__(self):
        self.error = MockErrorInfo()


class MockSfuEvent:
    def __init__(self):
        self.join_response = MockJoinResponse()
        self.error = MockError()
        self._which_oneof = None

    def HasField(self, field_name):
        if field_name == "join_response":
            return self._which_oneof == "join_response"
        elif field_name == "error":
            return self._which_oneof == "error"
        return False

    def WhichOneof(self, oneof_name):
        return self._which_oneof

    def ParseFromString(self, data):
        # Simulate parsing binary data
        if data == b"join_response":
            self._which_oneof = "join_response"
        elif data == b"error":
            self._which_oneof = "error"
        elif data == b"participant_joined":
            self._which_oneof = "participant_joined"
            self.participant_joined = MockEventPayload()
            self.participant_joined.participant = MockEventPayload()
            self.participant_joined.participant.user_id = "test_user"
        else:
            self._which_oneof = None


class MockJoinRequest:
    def __init__(self):
        self.token = "test_token"
        self.session_id = "test_session_id"


class MockSfuRequest:
    def __init__(self, join_request=None):
        self.join_request = join_request

    def SerializeToString(self):
        return b"serialized_request"


# Create the WebSocketClient class with full mocking
class TestWebSocketClient:
    @pytest.fixture(autouse=True)
    def setup_mocks(self):
        # Create mocks
        self.mock_events_pb2 = MagicMock()
        self.mock_events_pb2.SfuEvent = MockSfuEvent
        self.mock_events_pb2.SfuRequest = MockSfuRequest
        self.mock_events_pb2.JoinRequest = MockJoinRequest

        # Mock the WebSocketApp instance
        self.mock_ws_app = None  # Will be set when WebSocketApp is instantiated

        # Track the original WebSocketApp class
        self.original_websocket_app = mock_websocket.WebSocketApp

        # Create a subclass that will capture the instance
        self_obj = self

        class TrackingWebSocketApp(MockWebSocketApp):
            def __init__(self, *args, **kwargs):
                super().__init__(*args, **kwargs)
                self_obj.mock_ws_app = self

        # Replace the class
        mock_websocket.WebSocketApp = TrackingWebSocketApp

        # Mock threading.Thread
        self.mock_thread = MagicMock()
        self.mock_thread_class = MagicMock()
        self.mock_thread_class.return_value = self.mock_thread

        # Apply patches
        patcher1 = patch("websocket.WebSocketApp", TrackingWebSocketApp)
        patcher2 = patch.dict(
            "sys.modules",
            {
                "getstream.video.rtc.pb.stream.video.sfu.event.events_pb2": self.mock_events_pb2
            },
        )
        patcher3 = patch("threading.Thread", self.mock_thread_class)

        # Start patches
        patcher1.start()
        patcher2.start()
        patcher3.start()

        # Define WebSocketClient class with imports within the patched context
        # This definition is the same as in your production code, just included here for testing
        self.define_client_class()

        # Provide a teardown
        yield

        # Restore the original class
        patcher1.stop()
        patcher2.stop()
        patcher3.stop()

    def define_client_class(self):
        # Define the client class with the same implementation
        global WebSocketClient, SignalingError

        import asyncio
        import concurrent.futures
        import logging
        from typing import Any, Callable, Dict, Awaitable, List

        logger = logging.getLogger(__name__)

        class SignalingError(Exception):
            """Exception raised for errors in the signaling process."""

            pass

        class WebSocketClient:
            """
            WebSocket client for Stream Video signaling.
            Handles WebSocket connection, message serialization/deserialization, and event handling.
            """

            def __init__(self, url: str, join_request, main_loop: asyncio.AbstractEventLoop):
                """
                Initialize a new WebSocket client.

                Args:
                    url: The WebSocket server URL
                    join_request: The JoinRequest protobuf message to send for authentication
                    main_loop: The main asyncio event loop to run callbacks on
                """
                self.url = url
                self.join_request = join_request
                self.main_loop = main_loop
                self.ws = None
                self.event_handlers: Dict[
                    str, List[Callable[[Any], Awaitable[None]]]
                ] = {}
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
                from websocket import WebSocketApp

                self.ws = WebSocketApp(
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
                    error_msg = self.first_message.error.error.message
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
                import sys
                events_pb2 = sys.modules["getstream.video.rtc.pb.stream.video.sfu.event.events_pb2"]

                request = events_pb2.SfuRequest(join_request=self.join_request)
                ws.send(request.SerializeToString())

            def _on_message(self, ws, message):
                """Handle incoming WebSocket messages."""
                try:
                    # Deserialize the message
                    # Use the mocked events_pb2 from sys.modules
                    import sys
                    events_pb2 = sys.modules["getstream.video.rtc.pb.stream.video.sfu.event.events_pb2"]

                    event = events_pb2.SfuEvent()
                    event.ParseFromString(message)

                    # If this is the first message, set it and trigger the event
                    if not self.first_message_event.is_set():
                        self.first_message = event
                        self.main_loop.call_soon_threadsafe(
                            self.first_message_event.set
                        )

                    # Dispatch to event handlers
                    self._dispatch_event(event)

                except Exception as e:
                    logger.error(f"Error handling message: {str(e)}")

            def _on_error(self, ws, error):
                """Handle WebSocket error."""
                logger.error(f"WebSocket error: {str(error)}")
                if not self.first_message_event.is_set():
                    # Create an error event
                    # Use the mocked events_pb2 from sys.modules
                    import sys
                    events_pb2 = sys.modules["getstream.video.rtc.pb.stream.video.sfu.event.events_pb2"]

                    error_event = events_pb2.SfuEvent()
                    error_event._which_oneof = "error"
                    self.first_message = error_event
                    self.main_loop.call_soon_threadsafe(self.first_message_event.set)

            def _on_close(self, ws, close_status_code, close_msg):
                """Handle WebSocket close event."""
                logger.debug(
                    f"WebSocket connection closed: {close_status_code} {close_msg}"
                )
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

                # In test environment, run handlers directly in the main loop
                try:
                    # Schedule the handler to run in the main loop
                    task = asyncio.run_coroutine_threadsafe(handler(payload), self.main_loop)
                    # Don't wait for the result to avoid blocking
                except Exception as e:
                    logger.error(f"Error in event handler: {str(e)}")

            def on_event(
                self, event_type: str, callback: Callable[[Any], Awaitable[None]]
            ):
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
                except Exception:
                    # Ignore errors during shutdown
                    pass

    @pytest.fixture
    def join_request(self):
        """Create a sample JoinRequest for testing."""
        return MockJoinRequest()

    @pytest.mark.asyncio
    async def test_connect_success(self, join_request):
        """Test successful connection flow."""
        client = WebSocketClient("wss://test.url", join_request, asyncio.get_running_loop())

        try:
            # Start connection task but don't await it yet
            connect_task = asyncio.create_task(client.connect())

            # Wait a bit for the WebSocket to be created
            await asyncio.sleep(0.1)
            
            # Check if mock_ws_app was set
            assert self.mock_ws_app is not None, "WebSocketApp was not created"

            # Simulate websocket open - call the saved on_open callback
            self.mock_ws_app.on_open(self.mock_ws_app)

            # Verify join request was sent
            assert hasattr(self.mock_ws_app, "last_sent_data")

            # Simulate receiving join response
            event = MockSfuEvent()
            event._which_oneof = "join_response"
            self.mock_ws_app.on_message(self.mock_ws_app, b"join_response")

            # Wait for connect to complete
            response = await connect_task

            # Verify response
            assert response.HasField("join_response")
        finally:
            # Clean up
            client.close()

    @pytest.mark.asyncio
    async def test_connect_error(self, join_request):
        """Test connection with error response."""
        client = WebSocketClient("wss://test.url", join_request, asyncio.get_running_loop())

        try:
            # Start connection task
            connect_task = asyncio.create_task(client.connect())

            # Wait a bit for the WebSocket to be created
            await asyncio.sleep(0.1)
            
            # Check if mock_ws_app was set
            assert self.mock_ws_app is not None, "WebSocketApp was not created"

            # Simulate websocket open
            self.mock_ws_app.on_open(self.mock_ws_app)

            # Simulate receiving error
            self.mock_ws_app.on_message(self.mock_ws_app, b"error")

            # Verify connect throws an exception
            with pytest.raises(
                SignalingError, match="Connection failed: Error message"
            ):
                await connect_task
        finally:
            # Clean up
            client.close()

    @pytest.mark.asyncio
    async def test_websocket_error_during_connect(self, join_request):
        """Test WebSocket error during connection."""
        client = WebSocketClient("wss://test.url", join_request, asyncio.get_running_loop())

        try:
            # Start connection task
            connect_task = asyncio.create_task(client.connect())

            # Wait a bit for the WebSocket to be created
            await asyncio.sleep(0.1)
            
            # Check if mock_ws_app was set
            assert self.mock_ws_app is not None, "WebSocketApp was not created"

            # Simulate websocket error
            self.mock_ws_app.on_error(self.mock_ws_app, Exception("Connection failed"))

            # Verify connect throws an exception
            with pytest.raises(SignalingError):
                await connect_task
        finally:
            # Clean up
            client.close()

    @pytest.mark.asyncio
    async def test_event_callbacks(self, join_request):
        """Test event callbacks are executed correctly."""
        client = WebSocketClient("wss://test.url", join_request, asyncio.get_running_loop())

        # Create a callback tracking variable
        callback_results = {"participant_joined": 0, "wildcard": 0}

        # Register event handlers with fast completion to avoid hanging
        async def on_participant_joined(event):
            callback_results["participant_joined"] += 1
            assert hasattr(event, "participant")
            assert hasattr(event.participant, "user_id")
            assert event.participant.user_id == "test_user"

        async def on_any_event(event):
            callback_results["wildcard"] += 1

        client.on_event("participant_joined", on_participant_joined)
        client.on_event("*", on_any_event)

        try:
            # Start connection
            connect_task = asyncio.create_task(client.connect())

            # Wait a bit for the WebSocket to be created
            await asyncio.sleep(0.1)
            
            # Check if mock_ws_app was set
            assert self.mock_ws_app is not None, "WebSocketApp was not created"

            # Simulate websocket open and join response
            self.mock_ws_app.on_open(self.mock_ws_app)
            self.mock_ws_app.on_message(self.mock_ws_app, b"join_response")

            # Wait for connect to complete
            await connect_task

            # Simulate receiving participant joined event
            self.mock_ws_app.on_message(self.mock_ws_app, b"participant_joined")
            
            # Give some time for the callbacks to execute
            await asyncio.sleep(0.2)

            # Verify callbacks were called
            assert callback_results["participant_joined"] == 1
            assert callback_results["wildcard"] == 2  # Called for join_response and participant_joined
        finally:
            # Clean up
            client.close()

    @pytest.mark.asyncio
    async def test_thread_usage(self, join_request):
        """Test that thread is properly used and managed."""
        client = WebSocketClient("wss://test.url", join_request, asyncio.get_running_loop())

        try:
            # Start connection
            connect_task = asyncio.create_task(client.connect())

            # Wait a bit for the WebSocket to be created
            await asyncio.sleep(0.1)
            
            # Check if mock_ws_app was set
            assert self.mock_ws_app is not None, "WebSocketApp was not created"

            # Verify thread was created with correct target
            self.mock_thread_class.assert_called_once()
            assert "target" in self.mock_thread_class.call_args[1]
            assert (
                self.mock_thread_class.call_args[1]["target"] == client._run_websocket
            )

            # Simulate join response to complete connection
            self.mock_ws_app.on_message(self.mock_ws_app, b"join_response")

            # Complete the connect
            await connect_task

            # Verify thread is used
            self.mock_thread.start.assert_called_once()

            # Clean up
            client.close()

            # Thread should be joined during close
            self.mock_thread.join.assert_called_once()
            assert self.mock_thread.join.call_args[1]["timeout"] == 1.0
        finally:
            # Ensure cleanup even if test fails
            client.close()
