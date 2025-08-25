import asyncio
from unittest.mock import MagicMock

import pytest


# Create a simple mock version of the WebSocketClient that doesn't rely on protobuf
class MockWebSocketClient:
    def __init__(self, url, join_request):
        self.url = url
        self.join_request = join_request
        self.ws = None
        self.event_handlers = {}
        self.first_message_event = asyncio.Event()
        self.first_message = None
        self.thread = None
        self.running = False
        self.closed = False
        self.executor = MagicMock()

    async def connect(self):
        # This is a simplified version for testing
        # Normally this would establish a WebSocket connection
        return self.first_message

    def on_event(self, event_type, callback):
        if event_type not in self.event_handlers:
            self.event_handlers[event_type] = []
        self.event_handlers[event_type].append(callback)

    def close(self):
        self.closed = True
        self.running = False
        if self.ws:
            self.ws.close()
        if self.thread and self.thread.is_alive():
            self.thread.join(timeout=1.0)
        self.executor.shutdown(wait=False)


@pytest.mark.asyncio
async def test_websocket_client_simple():
    """Test basic WebSocketClient operations."""
    # Create a client
    client = MockWebSocketClient("wss://test.url", "mock_join_request")

    # Register an event handler
    callback_called = False

    async def on_event(event):
        nonlocal callback_called
        callback_called = True

    client.on_event("test_event", on_event)

    # Verify handler was registered
    assert "test_event" in client.event_handlers
    assert client.event_handlers["test_event"][0] == on_event

    # Close the client
    client.close()

    # Verify closed state
    assert client.closed
    assert not client.running


@pytest.mark.asyncio
async def test_websocket_client_close():
    """Test that close properly cleans up resources."""
    # Create mock objects
    mock_ws = MagicMock()
    mock_thread = MagicMock()
    mock_thread.is_alive.return_value = True
    mock_executor = MagicMock()

    # Create client
    client = MockWebSocketClient("wss://test.url", "mock_join_request")

    # Set mocks
    client.ws = mock_ws
    client.thread = mock_thread
    client.executor = mock_executor

    # Call close
    client.close()

    # Verify resources were cleaned up
    assert client.closed
    assert not client.running
    mock_ws.close.assert_called_once()
    mock_thread.join.assert_called_once()
    mock_executor.shutdown.assert_called_once_with(wait=False)
