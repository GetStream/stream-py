import asyncio
import pytest
import threading
from unittest.mock import patch

from getstream.video.rtc.signaling import WebSocketClient, SignalingError
from getstream.video.rtc.pb.stream.video.sfu.event import events_pb2


class TestWebSocketClient:
    @pytest.fixture
    def join_request(self):
        """Create a sample JoinRequest for testing."""
        return events_pb2.JoinRequest(token="test_token", session_id="test_session_id")

    @pytest.fixture
    def mock_websocket(self):
        """Create a mock WebSocketApp."""
        with patch("getstream.video.rtc.signaling.websocket.WebSocketApp") as mock_ws:
            # Configure the mock
            instance = mock_ws.return_value

            # Make run_forever block until the WebSocket is closed
            def run_forever_side_effect():
                # Keep running until the WebSocket is closed
                while hasattr(instance, "_keep_running") and instance._keep_running:
                    import time

                    time.sleep(0.01)

            instance.run_forever.side_effect = run_forever_side_effect
            instance._keep_running = True

            # Mock close to stop the run_forever loop
            def close_side_effect():
                instance._keep_running = False

            instance.close.side_effect = close_side_effect
            yield mock_ws

    @pytest.mark.asyncio
    async def test_connect_success(self, join_request, mock_websocket):
        """Test successful connection flow."""
        # Create client
        client = WebSocketClient(
            "wss://test.url", join_request, asyncio.get_running_loop()
        )

        # Prepare a successful response
        success_response = events_pb2.SfuEvent()
        success_response.join_response.reconnected = False
        success_response_bytes = success_response.SerializeToString()

        # Start connection
        connect_task = asyncio.create_task(client.connect())

        # Wait briefly for connection to start
        await asyncio.sleep(0.1)

        # Verify WebSocketApp was created with correct params
        mock_websocket.assert_called_once_with(
            "wss://test.url",
            on_open=client._on_open,
            on_message=client._on_message,
            on_error=client._on_error,
            on_close=client._on_close,
        )

        # Simulate websocket open
        on_open_callback = mock_websocket.call_args[1]["on_open"]
        on_open_callback(mock_websocket.return_value)

        # Verify join request was sent
        mock_websocket.return_value.send.assert_called_once()
        sent_bytes = mock_websocket.return_value.send.call_args[0][0]

        # Parse the sent message to verify it's a JoinRequest
        sent_message = events_pb2.SfuRequest()
        sent_message.ParseFromString(sent_bytes)
        assert sent_message.HasField("join_request")
        assert sent_message.join_request.token == "test_token"

        # Simulate receiving join response
        on_message_callback = mock_websocket.call_args[1]["on_message"]
        on_message_callback(mock_websocket.return_value, success_response_bytes)

        # Wait for connect to complete
        response = await connect_task

        # Verify response
        assert response.HasField("join_response")
        assert response.join_response.reconnected is False

        # Clean up
        client.close()

    @pytest.mark.asyncio
    async def test_connect_error(self, join_request, mock_websocket):
        """Test connection with error response."""
        # Create client
        client = WebSocketClient(
            "wss://test.url", join_request, asyncio.get_running_loop()
        )

        # Prepare an error response
        error_response = events_pb2.SfuEvent()
        error_response.error.error.code = 403
        error_response.error.error.message = "Unauthorized"
        error_response_bytes = error_response.SerializeToString()

        # Start connection
        connect_task = asyncio.create_task(client.connect())

        # Wait briefly for connection to start
        await asyncio.sleep(0.1)

        # Simulate websocket open
        on_open_callback = mock_websocket.call_args[1]["on_open"]
        on_open_callback(mock_websocket.return_value)

        # Simulate receiving error
        on_message_callback = mock_websocket.call_args[1]["on_message"]
        on_message_callback(mock_websocket.return_value, error_response_bytes)

        # Verify connect throws an exception
        with pytest.raises(SignalingError, match="Connection failed: Unauthorized"):
            await connect_task

        # Clean up
        client.close()

    @pytest.mark.asyncio
    async def test_websocket_error_during_connect(self, join_request, mock_websocket):
        """Test WebSocket error during connection."""
        # Create client
        client = WebSocketClient(
            "wss://test.url", join_request, asyncio.get_running_loop()
        )

        # Start connection
        connect_task = asyncio.create_task(client.connect())

        # Wait briefly for connection to start
        await asyncio.sleep(0.1)

        # Simulate websocket error
        on_error_callback = mock_websocket.call_args[1]["on_error"]
        on_error_callback(mock_websocket.return_value, Exception("Connection failed"))

        # Verify connect throws an exception
        with pytest.raises(
            SignalingError, match="Connection failed: Connection failed"
        ):
            await connect_task

        # Clean up
        client.close()

    @pytest.mark.asyncio
    async def test_event_callbacks(self, join_request, mock_websocket):
        """Test event callbacks are executed correctly."""
        # Create client
        client = WebSocketClient(
            "wss://test.url", join_request, asyncio.get_running_loop()
        )

        # Prepare a successful join response first
        join_response = events_pb2.SfuEvent()
        join_response.join_response.reconnected = False
        join_response_bytes = join_response.SerializeToString()

        # Create a callback tracking variable
        callback_results = {"participant_joined": 0, "wildcard": 0}

        # Register event handlers
        async def on_participant_joined(event):
            callback_results["participant_joined"] += 1
            assert event.participant.user_id == "test_user"

        async def on_any_event(event):
            callback_results["wildcard"] += 1

        client.on_event("participant_joined", on_participant_joined)
        client.on_event("*", on_any_event)

        # Start connection
        connect_task = asyncio.create_task(client.connect())

        # Wait briefly for connection to start
        await asyncio.sleep(0.1)

        # Simulate websocket open and join response
        on_open_callback = mock_websocket.call_args[1]["on_open"]
        on_open_callback(mock_websocket.return_value)

        on_message_callback = mock_websocket.call_args[1]["on_message"]
        on_message_callback(mock_websocket.return_value, join_response_bytes)

        # Wait for connect to complete
        await connect_task

        # Prepare a participant joined event
        participant_event = events_pb2.SfuEvent()
        participant_event.participant_joined.participant.user_id = "test_user"
        participant_bytes = participant_event.SerializeToString()

        # Simulate receiving participant joined event
        on_message_callback(mock_websocket.return_value, participant_bytes)

        # Wait for callbacks to be processed
        await asyncio.sleep(0.1)

        # Verify callbacks were called
        assert callback_results["participant_joined"] == 1
        assert (
            callback_results["wildcard"] == 2
        )  # Called for join_response and participant_joined

        # Clean up
        client.close()

    @pytest.mark.asyncio
    async def test_thread_usage(self, join_request, mock_websocket):
        """Test that thread is properly used and managed."""
        # Create client
        client = WebSocketClient(
            "wss://test.url", join_request, asyncio.get_running_loop()
        )

        # Mock threading.Thread to capture usage
        with patch("threading.Thread", wraps=threading.Thread) as mock_thread:
            # Start connection
            connect_task = asyncio.create_task(client.connect())

            # Wait briefly for thread creation
            await asyncio.sleep(0.1)

            # Verify thread was created with correct target
            # Check that at least one thread was created with the WebSocket target
            websocket_thread_calls = [
                call
                for call in mock_thread.call_args_list
                if call[1].get("target") == client._run_websocket
            ]
            assert len(websocket_thread_calls) == 1

            # Simulate join response to complete connection
            join_response = events_pb2.SfuEvent()
            join_response.join_response.reconnected = False
            on_message_callback = mock_websocket.call_args[1]["on_message"]
            on_message_callback(
                mock_websocket.return_value, join_response.SerializeToString()
            )

            # Complete the connect
            await connect_task

            # Verify thread is running
            assert client.thread is not None
            assert client.thread.is_alive()

            # Clean up
            client.close()

            # Thread should be joined during close
            assert not client.running
