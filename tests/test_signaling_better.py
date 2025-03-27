import pytest
from unittest.mock import MagicMock, patch

# Mock optional dependencies to avoid import errors
import sys

mock_aiortc = MagicMock()
mock_aiortc.__version__ = "1.0.0"  # Add mock version
sys.modules["aiortc"] = mock_aiortc

# Mock websocket module
mock_websocket = MagicMock()
mock_websocket.WebSocketApp = MagicMock
sys.modules["websocket"] = mock_websocket


# Create full mock versions of all dependencies
class MockSfuRequest:
    def __init__(self, **kwargs):
        for key, value in kwargs.items():
            setattr(self, key, value)

    def SerializeToString(self):
        return b"serialized_data"


class MockSfuEvent:
    def __init__(self):
        self.join_response = MagicMock()
        self.error = MockErrorEvent()
        self._field = None

    def HasField(self, field):
        return field == self._field

    def ParseFromString(self, data):
        # Just a stub implementation
        pass

    def WhichOneof(self, field_name):
        return "join_response"  # Default for tests


class MockErrorEvent:
    def __init__(self):
        self.error = MockError()


class MockError:
    def __init__(self):
        self.description = "Test error"


class MockJoinRequest:
    def __init__(self):
        pass


# Create the test module with all mocks
mock_events_pb2 = MagicMock()
mock_events_pb2.SfuRequest = MockSfuRequest
mock_events_pb2.SfuEvent = MockSfuEvent
mock_events_pb2.JoinRequest = MockJoinRequest


# Create a Module Factory for patching
class ModuleFactory:
    @staticmethod
    def create_events_pb2():
        return mock_events_pb2


# Now we can test the WebSocketClient with our mocks
@pytest.mark.asyncio
async def test_websocket_client_initialization():
    """Test WebSocketClient initialization."""
    # Patch the dependencies
    with patch.dict(
        "sys.modules",
        {"getstream.video.rtc.pb.stream.video.sfu.event.events_pb2": mock_events_pb2},
    ):
        # Import the client after patching
        from getstream.video.rtc.signaling import WebSocketClient

        # Create a client
        join_request = MockJoinRequest()
        client = WebSocketClient("wss://test.url", join_request)

        # Verify initial state
        assert client.url == "wss://test.url"
        assert client.join_request is join_request
        assert client.ws is None
        assert client.event_handlers == {}
        assert client.first_message is None
        assert client.thread is None
        assert client.running is False
        assert client.closed is False


@pytest.mark.asyncio
async def test_websocket_client_event_registration():
    """Test event handler registration."""
    # Patch the dependencies
    with patch.dict(
        "sys.modules",
        {"getstream.video.rtc.pb.stream.video.sfu.event.events_pb2": mock_events_pb2},
    ):
        # Import the client after patching
        from getstream.video.rtc.signaling import WebSocketClient

        # Create a client
        join_request = MockJoinRequest()
        client = WebSocketClient("wss://test.url", join_request)

        # Register event handlers
        async def handler1(event):
            pass

        async def handler2(event):
            pass

        client.on_event("test_event", handler1)
        client.on_event("test_event", handler2)
        client.on_event("*", handler1)

        # Verify handlers were registered
        assert len(client.event_handlers["test_event"]) == 2
        assert client.event_handlers["test_event"][0] is handler1
        assert client.event_handlers["test_event"][1] is handler2
        assert len(client.event_handlers["*"]) == 1
        assert client.event_handlers["*"][0] is handler1


@pytest.mark.asyncio
async def test_websocket_client_direct_methods():
    """Test WebSocketClient methods directly without connecting."""
    # Patch the dependencies
    with patch.dict(
        "sys.modules",
        {"getstream.video.rtc.pb.stream.video.sfu.event.events_pb2": mock_events_pb2},
    ):
        # Import the client after patching
        from getstream.video.rtc.signaling import WebSocketClient

        # Create a client with mocked dependencies
        join_request = MockJoinRequest()
        client = WebSocketClient("wss://test.url", join_request)

        # Create mocks for testing callbacks
        mock_ws = MagicMock()

        # Test on_open callback directly
        client._on_open(mock_ws)

        # Verify send was called with a serialized request
        mock_ws.send.assert_called_once_with(b"serialized_data")

        # Test on_message callback
        event = MockSfuEvent()
        event._field = "join_response"

        # Patch SfuEvent.ParseFromString to return our mock event
        with patch.object(mock_events_pb2.SfuEvent, "ParseFromString"):
            client._on_message(mock_ws, b"test_message")

        # Test on_close callback
        client.running = True
        client._on_close(mock_ws, 1000, "Normal closure")

        # Verify running was set to False
        assert not client.running

        # Test on_error callback
        client.first_message = None
        client._on_error(mock_ws, Exception("Test error"))

        # Verify an error event was created
        assert client.first_message is not None
        assert client.first_message.error.error.description == "Test error"


@pytest.mark.asyncio
async def test_websocket_client_close():
    """Test that close properly cleans up resources."""
    # Patch the dependencies
    with patch.dict(
        "sys.modules",
        {"getstream.video.rtc.pb.stream.video.sfu.event.events_pb2": mock_events_pb2},
    ):
        # Import the client after patching
        from getstream.video.rtc.signaling import WebSocketClient

        # Create a client
        join_request = MockJoinRequest()
        client = WebSocketClient("wss://test.url", join_request)

        # Create mocks for the resources
        client.ws = MagicMock()
        client.thread = MagicMock()
        client.thread.is_alive.return_value = True
        client.executor = MagicMock()
        client.event_loop = MagicMock()

        # Add some handlers to verify they're cleared
        async def handler(event):
            pass

        client.on_event("test", handler)

        # Call close
        client.close()

        # Verify resources were cleaned up
        assert client.closed
        assert not client.running
        client.ws.close.assert_called_once()
        client.thread.join.assert_called_once_with(timeout=1.0)
        client.executor.shutdown.assert_called_once_with(wait=False)
        assert not client.event_handlers  # Should be empty

        # Call close again - should be a no-op
        client.close()

        # Verify no additional calls were made
        client.ws.close.assert_called_once()
        client.thread.join.assert_called_once()
        client.executor.shutdown.assert_called_once()
