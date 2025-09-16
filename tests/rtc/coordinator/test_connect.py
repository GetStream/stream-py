"""
Tests for StreamAPIWS connect and disconnect functionality.
"""

import asyncio
import json

import pytest
import websockets

from getstream.video.rtc.coordinator.ws import StreamAPIWS, Call
from getstream.video.rtc.coordinator.errors import (
    StreamWSAuthError,
    StreamWSConnectionError,
)
from getstream.stream import Stream


@pytest.mark.asyncio
async def test_simple_connection_debug():
    """Simple test to debug websocket server handler signature."""

    # Very simple handler that just echoes back
    async def echo_handler(websocket):
        try:
            while True:
                message = await websocket.recv()
                await websocket.send(message)
        except websockets.exceptions.ConnectionClosed:
            pass

    # Start server without path in handler
    server = await websockets.serve(echo_handler, "localhost", 0)
    port = server.sockets[0].getsockname()[1]
    server_uri = f"ws://localhost:{port}"

    try:
        # Test basic websocket functionality
        websocket = await websockets.connect(server_uri)
        await websocket.send("test")
        response = await websocket.recv()
        assert response == "test"
        await websocket.close()

    finally:
        server.close()
        await server.wait_closed()


@pytest.mark.asyncio
async def test_successful_connection(client: Stream):
    """Test successful connection and authentication."""

    # Mock server that sends connection.ok
    async def mock_server(websocket):
        try:
            # Wait for auth payload
            auth_message = await websocket.recv()
            auth_data = json.loads(auth_message)

            # Verify auth payload structure
            assert "token" in auth_data
            assert "products" in auth_data
            assert "user_details" in auth_data
            assert auth_data["products"] == ["video"]

            # Send successful connection response
            response = {"type": "connection.ok", "message": "Authentication successful"}
            await websocket.send(json.dumps(response))

        except websockets.exceptions.ConnectionClosed:
            pass

    # Start mock server
    server = await websockets.serve(mock_server, "localhost", 0)
    port = server.sockets[0].getsockname()[1]
    server_uri = f"ws://localhost:{port}"
    call = Call(client.video, "default")

    try:
        # Create client and connect
        client = StreamAPIWS(
            call,
            user_details={"id": "test_user"},
            uri=server_uri,
        )

        # Test connection
        result = await client.connect()

        # Verify result
        assert result["type"] == "connection.ok"
        assert result["message"] == "Authentication successful"
        assert client.connected is True

        # Disconnect
        await client.disconnect()
        assert client.connected is False

    finally:
        server.close()
        await server.wait_closed()


@pytest.mark.asyncio
async def test_authentication_error(client: Stream):
    """Test authentication failure handling."""

    # Mock server that sends error response
    async def mock_server(websocket):
        try:
            # Wait for auth payload
            _ = await websocket.recv()

            # Send error response
            error_response = {
                "type": "error",
                "error": "invalid_token",
                "message": "Authentication failed",
            }
            await websocket.send(json.dumps(error_response))

        except websockets.exceptions.ConnectionClosed:
            pass

    # Start mock server
    server = await websockets.serve(mock_server, "localhost", 0)
    port = server.sockets[0].getsockname()[1]
    server_uri = f"ws://localhost:{port}"
    call = Call(client.video, "default")

    try:
        # Create client
        client = StreamAPIWS(
            call,
            user_details={"id": "test_user"},
            uri=server_uri,
        )

        # Test that authentication error is raised
        with pytest.raises(StreamWSAuthError) as exc_info:
            await client.connect()

        # Verify error message contains authentication failure info
        assert "Authentication failed" in str(exc_info.value)
        assert client.connected is False

    finally:
        server.close()
        await server.wait_closed()


@pytest.mark.asyncio
async def test_connection_error(client: Stream):
    """Test connection failure handling."""
    # Use an invalid URI to trigger connection error
    call = Call(client.video, "default")
    client = StreamAPIWS(
        call,
        user_details={"id": "test_user"},
        uri="ws://localhost:99999",  # Invalid port
    )

    # Test that connection error is raised
    with pytest.raises(StreamWSConnectionError):
        await client.connect()

    assert client.connected is False


@pytest.mark.asyncio
async def test_invalid_json_response(client: Stream):
    """Test handling of invalid JSON from server."""

    # Mock server that sends invalid JSON
    async def mock_server(websocket):
        try:
            # Wait for auth payload
            await websocket.recv()

            # Send invalid JSON
            await websocket.send("invalid json response")

        except websockets.exceptions.ConnectionClosed:
            pass

    # Start mock server
    server = await websockets.serve(mock_server, "localhost", 0)
    port = server.sockets[0].getsockname()[1]
    server_uri = f"ws://localhost:{port}"
    call = Call(client.video, "default")

    try:
        # Create client
        client = StreamAPIWS(
            call,
            user_details={"id": "test_user"},
            uri=server_uri,
        )

        # Test that connection error is raised for invalid JSON
        with pytest.raises(StreamWSConnectionError) as exc_info:
            await client.connect()

        assert "Invalid JSON from server" in str(exc_info.value)
        assert client.connected is False

    finally:
        server.close()
        await server.wait_closed()


@pytest.mark.asyncio
async def test_event_emission(client: Stream):
    """Test that events are properly emitted."""

    # Mock server that sends connection.ok
    async def mock_server(websocket):
        try:
            # Wait for auth payload
            await websocket.recv()

            # Send successful connection response
            response = {"type": "connection.ok", "data": {"session_id": "test_session"}}
            await websocket.send(json.dumps(response))

        except websockets.exceptions.ConnectionClosed:
            pass

    # Start mock server
    server = await websockets.serve(mock_server, "localhost", 0)
    port = server.sockets[0].getsockname()[1]
    server_uri = f"ws://localhost:{port}"
    call = Call(client.video, "default")

    try:
        # Create client
        client = StreamAPIWS(
            call,
            user_details={"id": "test_user"},
            uri=server_uri,
        )

        # Set up event listener
        events_received = []

        @client.on("connection.ok")
        def on_connection_ok(data):
            events_received.append(("connection.ok", data))

        # Connect and verify event emission
        result = await client.connect()

        # Verify event was emitted
        assert len(events_received) == 1
        assert events_received[0][0] == "connection.ok"
        assert events_received[0][1] == result

        await client.disconnect()

    finally:
        server.close()
        await server.wait_closed()


@pytest.mark.asyncio
async def test_auth_payload_structure(client: Stream):
    """Test that authentication payload has correct structure."""

    # Mock server that captures and validates auth payload
    captured_auth = None

    async def mock_server(websocket):
        nonlocal captured_auth
        try:
            # Capture auth payload
            auth_message = await websocket.recv()
            captured_auth = json.loads(auth_message)

            # Send successful response
            response = {"type": "connection.ok"}
            await websocket.send(json.dumps(response))

        except websockets.exceptions.ConnectionClosed:
            pass

    # Start mock server
    server = await websockets.serve(mock_server, "localhost", 0)
    port = server.sockets[0].getsockname()[1]
    server_uri = f"ws://localhost:{port}"
    call = Call(client.video, "default")

    try:
        # Create client
        client = StreamAPIWS(
            call,
            user_details={"id": "user_456", "name": "Test User"},
            uri=server_uri,
        )

        # Connect
        await client.connect()

        # Verify auth payload structure
        assert captured_auth is not None
        assert captured_auth["token"] == client.user_token
        assert captured_auth["products"] == ["video"]
        assert captured_auth["user_details"]["id"] == "user_456"
        assert captured_auth["user_details"]["name"] == "Test User"

        await client.disconnect()

    finally:
        server.close()
        await server.wait_closed()


@pytest.mark.asyncio
async def test_disconnect_without_connect(client: Stream):
    """Test that disconnect works even if never connected."""
    call = Call(client.video, "default")
    client = StreamAPIWS(
        call, user_details={"id": "test_user"}
    )

    # Should not raise an exception
    await client.disconnect()
    assert client.connected is False


@pytest.mark.asyncio
async def test_integration_test_simple(client: Stream):
    call = Call(client.video, "default")
    ws_client = StreamAPIWS(
        call, user_details={"id": "user_id"}
    )
    response = await ws_client.connect()
    assert response["type"] == "connection.ok"
    await ws_client.disconnect()


@pytest.mark.asyncio
async def test_integration_test_bad_auth_raises(client: Stream):
    call = Call(Stream(client.api_key, "api_sec").video, "default")
    ws_client = StreamAPIWS(call, user_details={"id": "xxx"})

    # Test that authentication error is raised with invalid token
    with pytest.raises(StreamWSAuthError) as exc_info:
        await ws_client.connect()

    # Verify error message contains authentication failure info
    assert "Authentication failed" in str(exc_info.value)
    assert "connection.error" in str(exc_info.value)
    assert ws_client.connected is False


@pytest.mark.asyncio
async def test_integration_test_simple_healthcheck(client: Stream):
    call = Call(client.video, "default")
    ws_client = StreamAPIWS(
        call,
        user_details={"id": "xx"},
        healthcheck_interval=2.0,
    )
    response = await ws_client.connect()
    assert response["type"] == "connection.ok"

    # Wait for a few heartbeat intervals to ensure the connection stays alive
    # The heartbeat mechanism should prevent disconnection
    await asyncio.sleep(5.0)

    # Verify connection is still alive
    assert ws_client.connected is True

    await ws_client.disconnect()


@pytest.mark.asyncio
async def test_integration_test_user_details_in_response(client: Stream):
    """Test that user details are returned in the 'me' field of the connection response."""
    user_details = {
        "id": "test_user_123",
        "name": "Test User yo",
    }

    call = Call(client.video, "default")
    ws_client = StreamAPIWS(
        call,
        user_details=user_details,
        healthcheck_interval=30.0,  # Long interval to avoid interference
    )

    response = await ws_client.connect()
    assert response["type"] == "connection.ok"

    # Verify that user information is returned in the "me" field
    assert "me" in response, "Expected 'me' field in connection response"
    me_field = response["me"]

    # Verify user details are present in the me field
    assert me_field["id"] == "test_user_123"
    assert me_field["name"] == "Test User yo"

    # Verify that server added additional fields
    assert "created_at" in me_field
    assert "updated_at" in me_field
    assert "online" in me_field
    assert me_field["online"] is True  # Should be online since we just connected

    await ws_client.disconnect()
