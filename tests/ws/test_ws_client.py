import asyncio
import json

import pytest
import pytest_asyncio
import websockets

from getstream.ws import StreamWS


def test_stream_ws_instantiation():
    ws = StreamWS(
        api_key="test-key",
        api_secret="test-secret",
        user_id="alice",
    )
    assert ws.api_key == "test-key"
    assert ws.user_id == "alice"
    assert not ws.connected


def test_ws_url_construction():
    ws = StreamWS(
        api_key="my-key",
        api_secret="my-secret",
        user_id="alice",
        base_url="https://chat.stream-io-api.com",
    )
    url = ws.ws_url
    assert url.startswith("wss://chat.stream-io-api.com/connect?")
    assert "api_key=my-key" in url
    assert "stream-auth-type=jwt" in url


def test_ws_url_construction_http():
    ws = StreamWS(
        api_key="k",
        api_secret="s",
        user_id="bob",
        base_url="http://localhost:3030",
    )
    url = ws.ws_url
    assert url.startswith("ws://localhost:3030/connect?")


@pytest_asyncio.fixture()
async def mock_server():
    """WS server that handles auth and keeps connections open."""
    auth_payloads = []
    connections = []

    client_messages = []

    async def handler(ws):
        connections.append(ws)
        raw = await ws.recv()
        msg = json.loads(raw)
        auth_payloads.append(msg)
        await ws.send(
            json.dumps(
                {
                    "type": "connection.ok",
                    "connection_id": "conn-123",
                    "me": {"id": msg["user_details"]["id"]},
                }
            )
        )
        try:
            async for raw_msg in ws:
                client_messages.append(json.loads(raw_msg))
        except websockets.exceptions.ConnectionClosed:
            pass

    async with websockets.serve(handler, "127.0.0.1", 0) as server:
        port = server.sockets[0].getsockname()[1]
        yield {
            "port": port,
            "auth_payloads": auth_payloads,
            "connections": connections,
            "client_messages": client_messages,
        }


@pytest.mark.asyncio
async def test_connect_and_authenticate(mock_server):
    ws = StreamWS(
        api_key="test-key",
        api_secret="test-secret",
        user_id="alice",
        base_url=f"http://127.0.0.1:{mock_server['port']}",
    )
    result = await ws.connect()

    assert ws.connected
    assert ws.connection_id == "conn-123"
    assert result["type"] == "connection.ok"

    auth = mock_server["auth_payloads"][0]
    assert "token" in auth
    assert auth["user_details"]["id"] == "alice"

    await ws.disconnect()


@pytest.mark.asyncio
async def test_event_dispatched_to_listener(mock_server):
    ws = StreamWS(
        api_key="k",
        api_secret="s" * 32,
        user_id="alice",
        base_url=f"http://127.0.0.1:{mock_server['port']}",
    )
    await ws.connect()

    received_events = []

    @ws.on("message.new")
    def on_message(event):
        received_events.append(event)

    server_ws = mock_server["connections"][0]
    await server_ws.send(json.dumps({"type": "message.new", "text": "hello"}))
    await asyncio.sleep(0.1)

    assert len(received_events) == 1
    assert received_events[0]["text"] == "hello"

    await ws.disconnect()


@pytest.mark.asyncio
async def test_heartbeat_sent(mock_server):
    ws = StreamWS(
        api_key="k",
        api_secret="s" * 32,
        user_id="alice",
        base_url=f"http://127.0.0.1:{mock_server['port']}",
        healthcheck_interval=0.1,
    )
    await ws.connect()

    # Wait long enough for at least 2 heartbeats
    await asyncio.sleep(0.35)

    heartbeats = [
        m for m in mock_server["client_messages"]
        if m.get("type") == "health.check"
    ]
    assert len(heartbeats) >= 2
    assert heartbeats[0]["client_id"] == "conn-123"

    await ws.disconnect()


@pytest.mark.asyncio
async def test_reconnect_on_server_close(mock_server):
    ws = StreamWS(
        api_key="k",
        api_secret="s" * 32,
        user_id="alice",
        base_url=f"http://127.0.0.1:{mock_server['port']}",
        healthcheck_interval=100,
        max_retries=3,
    )
    await ws.connect()
    assert ws.connected
    assert len(mock_server["connections"]) == 1

    # Server forcibly closes the connection
    await mock_server["connections"][0].close()

    # Wait for reconnect
    await asyncio.sleep(0.5)

    assert ws.connected
    # A second connection was made (the reconnect)
    assert len(mock_server["connections"]) == 2
    assert len(mock_server["auth_payloads"]) == 2

    await ws.disconnect()


@pytest_asyncio.fixture()
async def token_expiry_server():
    """Server that rejects the 2nd connection with code 40, then accepts the 3rd."""
    auth_payloads = []
    connect_count = 0

    async def handler(ws):
        nonlocal connect_count
        connect_count += 1
        raw = await ws.recv()
        msg = json.loads(raw)
        auth_payloads.append(msg)

        if connect_count == 2:
            # Reject with token expired
            await ws.send(
                json.dumps(
                    {
                        "type": "connection.error",
                        "error": {"code": 40, "message": "token expired"},
                    }
                )
            )
            return

        await ws.send(
            json.dumps(
                {
                    "type": "connection.ok",
                    "connection_id": f"conn-{connect_count}",
                    "me": {"id": msg["user_details"]["id"]},
                }
            )
        )
        try:
            async for _ in ws:
                pass
        except websockets.exceptions.ConnectionClosed:
            pass

    async with websockets.serve(handler, "127.0.0.1", 0) as server:
        port = server.sockets[0].getsockname()[1]
        yield {"port": port, "auth_payloads": auth_payloads}


@pytest.mark.asyncio
async def test_token_refresh_on_expired(token_expiry_server):
    ws = StreamWS(
        api_key="k",
        api_secret="s" * 32,
        user_id="alice",
        base_url=f"http://127.0.0.1:{token_expiry_server['port']}",
        healthcheck_interval=100,
        max_retries=5,
        backoff_base=0.05,
        backoff_max=0.1,
    )
    await ws.connect()

    # Server closes -> reconnect hits code 40 -> should refresh token and retry
    await ws._websocket.close()
    await asyncio.sleep(0.5)

    assert ws.connected
    # 3 auth attempts: initial, rejected (code 40), successful retry
    assert len(token_expiry_server["auth_payloads"]) == 3

    await ws.disconnect()
