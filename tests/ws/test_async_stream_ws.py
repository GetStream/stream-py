import json

import pytest
import pytest_asyncio
import websockets

from getstream import AsyncStream


@pytest_asyncio.fixture()
async def mock_server():
    """WS server that handles auth and keeps connections open."""
    connections = []

    async def handler(ws):
        connections.append(ws)
        raw = await ws.recv()
        msg = json.loads(raw)
        await ws.send(
            json.dumps(
                {
                    "type": "connection.ok",
                    "connection_id": "conn-int",
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
        yield {"port": port, "connections": connections}


@pytest.mark.asyncio
async def test_connect_ws_context_manager(mock_server):
    client = AsyncStream(
        api_key="k" * 32,
        api_secret="s" * 32,
        base_url=f"http://127.0.0.1:{mock_server['port']}",
    )
    async with client.connect_ws(user_id="alice") as ws:
        assert ws.connected
        assert ws.connection_id == "conn-int"
        assert ws.user_id == "alice"

    assert not ws.connected
    await client.aclose()


@pytest.mark.asyncio
async def test_aclose_disconnects_ws(mock_server):
    client = AsyncStream(
        api_key="k" * 32,
        api_secret="s" * 32,
        base_url=f"http://127.0.0.1:{mock_server['port']}",
    )
    async with client.connect_ws(user_id="bob") as ws:
        assert ws.connected

    await client.aclose()
    assert not ws.connected


@pytest.mark.asyncio
async def test_standalone_context_manager(mock_server):
    from getstream.ws import StreamWS

    async with StreamWS(
        api_key="k" * 32,
        api_secret="s" * 32,
        user_id="alice",
        base_url=f"http://127.0.0.1:{mock_server['port']}",
    ) as ws:
        assert ws.connected
        assert ws.connection_id == "conn-int"

    assert not ws.connected
