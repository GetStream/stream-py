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
            async for _ in ws:
                pass
        except websockets.exceptions.ConnectionClosed:
            pass

    async with websockets.serve(handler, "127.0.0.1", 0) as server:
        port = server.sockets[0].getsockname()[1]
        yield {
            "port": port,
            "auth_payloads": auth_payloads,
            "connections": connections,
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
