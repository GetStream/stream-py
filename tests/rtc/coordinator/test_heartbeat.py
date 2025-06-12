"""
Tests for StreamAPIWS heartbeat and reconnection functionality.
"""

import asyncio
import json
import pytest
import time
from unittest.mock import patch
import websockets

from getstream.video.rtc.coordinator.ws import StreamAPIWS
from getstream.video.rtc.coordinator.errors import (
    StreamWSConnectionError,
    StreamWSMaxRetriesExceeded,
)


@pytest.mark.asyncio
async def test_heartbeat_sent_periodically():
    """Test that heartbeat messages are sent at regular intervals."""
    heartbeats_received = []

    async def mock_server(websocket):
        try:
            # Wait for auth payload
            await websocket.recv()

            # Send connection.ok
            response = {"type": "connection.ok"}
            await websocket.send(json.dumps(response))

            # Collect heartbeat messages
            while True:
                message = await websocket.recv()
                data = json.loads(message)
                if data.get("type") == "health.check":
                    heartbeats_received.append(time.time())

        except websockets.exceptions.ConnectionClosed:
            pass

    server = await websockets.serve(mock_server, "localhost", 0)
    port = server.sockets[0].getsockname()[1]
    server_uri = f"ws://localhost:{port}"

    try:
        # Create client with short heartbeat interval for testing
        client = StreamAPIWS(
            api_key="test_key",
            token="test_token",
            user_details={"id": "test_user"},
            uri=server_uri,
            healthcheck_interval=0.1,  # 100ms for fast testing
        )

        # Connect and wait for a few heartbeats
        await client.connect()
        await asyncio.sleep(0.35)  # Wait for ~3 heartbeats
        await client.disconnect()

        # Verify heartbeats were sent
        assert (
            len(heartbeats_received) >= 2
        ), f"Expected at least 2 heartbeats, got {len(heartbeats_received)}"

        # Verify timing between heartbeats
        if len(heartbeats_received) >= 2:
            interval = heartbeats_received[1] - heartbeats_received[0]
            assert (
                0.08 <= interval <= 0.15
            ), f"Heartbeat interval should be ~0.1s, got {interval}"

    finally:
        server.close()
        await server.wait_closed()


@pytest.mark.asyncio
async def test_reconnect_on_heartbeat_timeout():
    """Test that reconnection is triggered when no messages are received within timeout."""
    connection_attempts = []

    async def mock_server(websocket):
        try:
            connection_attempts.append(time.time())

            # Wait for auth payload
            await websocket.recv()

            # Send connection.ok
            response = {"type": "connection.ok"}
            await websocket.send(json.dumps(response))

            # For first connection, just ignore heartbeats (simulate server silence)
            if len(connection_attempts) == 1:
                # Don't respond to anything, let it timeout
                await asyncio.sleep(2)  # Wait longer than the timeout
            else:
                # For reconnection, respond normally
                while True:
                    await websocket.recv()  # Ignore incoming messages

        except websockets.exceptions.ConnectionClosed:
            pass

    server = await websockets.serve(mock_server, "localhost", 0)
    port = server.sockets[0].getsockname()[1]
    server_uri = f"ws://localhost:{port}"

    try:
        # Create client with short timeout for testing
        client = StreamAPIWS(
            api_key="test_key",
            token="test_token",
            user_details={"id": "test_user"},
            uri=server_uri,
            healthcheck_interval=0.1,  # 100ms heartbeat interval
            healthcheck_timeout=0.2,  # 200ms timeout
            backoff_base=0.1,  # Fast reconnection for testing
            max_retries=3,
        )

        # Connect and wait for timeout + reconnection
        await client.connect()
        await asyncio.sleep(1)  # Wait for timeout and reconnection
        await client.disconnect()

        # Verify reconnection occurred
        assert (
            len(connection_attempts) >= 2
        ), f"Expected at least 2 connection attempts, got {len(connection_attempts)}"

    finally:
        server.close()
        await server.wait_closed()


@pytest.mark.asyncio
async def test_reconnect_on_connection_closed():
    """Test that reconnection is triggered when server closes the connection."""
    connection_attempts = []

    async def mock_server(websocket):
        try:
            connection_attempts.append(time.time())

            # Wait for auth payload
            await websocket.recv()

            # Send connection.ok
            response = {"type": "connection.ok"}
            await websocket.send(json.dumps(response))

            if len(connection_attempts) == 1:
                # Close connection after short delay to trigger reconnection
                await asyncio.sleep(0.1)
                await websocket.close()
            else:
                # For reconnection, stay connected
                while True:
                    await websocket.recv()

        except websockets.exceptions.ConnectionClosed:
            pass

    server = await websockets.serve(mock_server, "localhost", 0)
    port = server.sockets[0].getsockname()[1]
    server_uri = f"ws://localhost:{port}"

    try:
        client = StreamAPIWS(
            api_key="test_key",
            token="test_token",
            user_details={"id": "test_user"},
            uri=server_uri,
            backoff_base=0.1,  # Fast reconnection for testing
            max_retries=3,
        )

        # Connect and wait for close + reconnection
        await client.connect()
        await asyncio.sleep(0.5)  # Wait for close and reconnection
        await client.disconnect()

        # Verify reconnection occurred
        assert (
            len(connection_attempts) >= 2
        ), f"Expected at least 2 connection attempts, got {len(connection_attempts)}"

    finally:
        server.close()
        await server.wait_closed()


@pytest.mark.asyncio
async def test_max_retries_exceeded():
    """Test that StreamWSMaxRetriesExceeded is raised when all retries fail."""

    # Server that always closes immediately
    async def failing_server(websocket):
        await websocket.close()

    server = await websockets.serve(failing_server, "localhost", 0)
    port = server.sockets[0].getsockname()[1]
    server_uri = f"ws://localhost:{port}"

    try:
        # Mock asyncio.sleep to make test run faster
        with patch("asyncio.sleep", side_effect=lambda x: asyncio.sleep(0.01)):
            client = StreamAPIWS(
                api_key="test_key",
                token="test_token",
                user_details={"id": "test_user"},
                uri=server_uri,
                healthcheck_interval=0.1,
                healthcheck_timeout=0.2,
                backoff_base=0.1,
                max_retries=2,  # Small number for testing
            )

            # Connect should eventually fail with max retries exceeded
            with pytest.raises((StreamWSConnectionError, StreamWSMaxRetriesExceeded)):
                await client.connect()
                # Wait a bit to let reconnection attempts happen
                await asyncio.sleep(0.5)

            assert not client.connected

    finally:
        server.close()
        await server.wait_closed()


@pytest.mark.asyncio
async def test_message_reception_updates_last_received():
    """Test that receiving messages updates the last received timestamp."""

    async def mock_server(websocket):
        try:
            # Wait for auth payload
            await websocket.recv()

            # Send connection.ok
            response = {"type": "connection.ok"}
            await websocket.send(json.dumps(response))

            # Send additional messages
            await asyncio.sleep(0.1)
            await websocket.send(json.dumps({"type": "test.message", "data": "test"}))

            await asyncio.sleep(0.1)
            await websocket.send(
                json.dumps({"type": "another.message", "data": "test2"})
            )

            # Keep server alive
            await asyncio.sleep(1)

        except websockets.exceptions.ConnectionClosed:
            pass

    server = await websockets.serve(mock_server, "localhost", 0)
    port = server.sockets[0].getsockname()[1]
    server_uri = f"ws://localhost:{port}"

    try:
        client = StreamAPIWS(
            api_key="test_key",
            token="test_token",
            user_details={"id": "test_user"},
            uri=server_uri,
            healthcheck_interval=1.0,  # Long interval so heartbeats don't interfere
            healthcheck_timeout=2.0,
        )

        messages_received = []

        @client.on("test.message")
        def on_test_message(data):
            messages_received.append(("test.message", time.time()))

        @client.on("another.message")
        def on_another_message(data):
            messages_received.append(("another.message", time.time()))

        # Connect and wait for messages
        initial_time = time.time()
        await client.connect()
        await asyncio.sleep(0.5)  # Wait for messages to arrive

        # Verify messages were received
        assert (
            len(messages_received) >= 2
        ), f"Expected at least 2 messages, got {len(messages_received)}"

        # Verify last_received was updated (should be more recent than initial connection)
        assert client._last_received > initial_time

        await client.disconnect()

    finally:
        server.close()
        await server.wait_closed()


@pytest.mark.asyncio
async def test_background_tasks_cancelled_on_disconnect():
    """Test that background tasks are properly cancelled when disconnecting."""

    async def mock_server(websocket):
        try:
            await websocket.recv()  # auth
            await websocket.send(json.dumps({"type": "connection.ok"}))
            await asyncio.sleep(1)  # Keep server alive
        except websockets.exceptions.ConnectionClosed:
            pass

    server = await websockets.serve(mock_server, "localhost", 0)
    port = server.sockets[0].getsockname()[1]
    server_uri = f"ws://localhost:{port}"

    try:
        client = StreamAPIWS(
            api_key="test_key",
            token="test_token",
            user_details={"id": "test_user"},
            uri=server_uri,
        )

        # Connect
        await client.connect()

        # Verify tasks are running
        assert client._reader_task is not None
        assert client._heartbeat_task is not None
        assert not client._reader_task.done()
        assert not client._heartbeat_task.done()

        # Disconnect
        await client.disconnect()

        # Verify tasks are cancelled
        assert client._reader_task is None
        assert client._heartbeat_task is None

    finally:
        server.close()
        await server.wait_closed()


@pytest.mark.asyncio
async def test_heartbeat_includes_client_id():
    """Test that heartbeats include client_id when available."""

    # Track sent messages
    sent_messages = []

    # Mock server that includes connection_id in response
    async def mock_server(websocket):
        try:
            # Wait for auth payload
            await websocket.recv()

            # Send successful connection response with connection_id
            response = {
                "type": "connection.ok",
                "connection_id": "test-connection-123",
                "message": "Authentication successful",
            }
            await websocket.send(json.dumps(response))

            # Receive and track heartbeat messages
            while True:
                try:
                    message = await websocket.recv()
                    sent_messages.append(json.loads(message))
                except websockets.exceptions.ConnectionClosed:
                    break

        except websockets.exceptions.ConnectionClosed:
            pass

    # Start mock server
    server = await websockets.serve(mock_server, "localhost", 0)
    port = server.sockets[0].getsockname()[1]
    server_uri = f"ws://localhost:{port}"

    try:
        # Create client with short heartbeat interval
        client = StreamAPIWS(
            api_key="test_key",
            token="test_token",
            user_details={"id": "test_user"},
            uri=server_uri,
            healthcheck_interval=0.1,  # 100ms
        )

        # Connect and wait for a heartbeat
        await client.connect()
        await asyncio.sleep(0.2)  # Wait for at least one heartbeat

        # Verify that heartbeats were sent and include client_id
        assert len(sent_messages) > 0

        # Check that heartbeat messages include client_id
        heartbeat_messages = [
            msg for msg in sent_messages if msg.get("type") == "health.check"
        ]
        assert len(heartbeat_messages) > 0

        for heartbeat in heartbeat_messages:
            assert heartbeat["type"] == "health.check"
            assert heartbeat["client_id"] == "test-connection-123"

        await client.disconnect()

    finally:
        server.close()
        await server.wait_closed()


@pytest.mark.asyncio
async def test_heartbeat_without_client_id():
    """Test that heartbeats work when no client_id is available."""

    # Track sent messages
    sent_messages = []

    # Mock server that doesn't include connection_id in response
    async def mock_server(websocket):
        try:
            # Wait for auth payload
            await websocket.recv()

            # Send successful connection response without connection_id
            response = {"type": "connection.ok", "message": "Authentication successful"}
            await websocket.send(json.dumps(response))

            # Receive and track heartbeat messages
            while True:
                try:
                    message = await websocket.recv()
                    sent_messages.append(json.loads(message))
                except websockets.exceptions.ConnectionClosed:
                    break

        except websockets.exceptions.ConnectionClosed:
            pass

    # Start mock server
    server = await websockets.serve(mock_server, "localhost", 0)
    port = server.sockets[0].getsockname()[1]
    server_uri = f"ws://localhost:{port}"

    try:
        # Create client with short heartbeat interval
        client = StreamAPIWS(
            api_key="test_key",
            token="test_token",
            user_details={"id": "test_user"},
            uri=server_uri,
            healthcheck_interval=0.1,  # 100ms
        )

        # Connect and wait for a heartbeat
        await client.connect()
        await asyncio.sleep(0.2)  # Wait for at least one heartbeat

        # Verify that heartbeats were sent but don't include client_id
        assert len(sent_messages) > 0

        # Check that heartbeat messages don't include client_id
        heartbeat_messages = [
            msg for msg in sent_messages if msg.get("type") == "health.check"
        ]
        assert len(heartbeat_messages) > 0

        for heartbeat in heartbeat_messages:
            assert heartbeat["type"] == "health.check"
            assert "client_id" not in heartbeat

        await client.disconnect()

    finally:
        server.close()
        await server.wait_closed()
