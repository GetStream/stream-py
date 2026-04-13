import json

import pytest
import pytest_asyncio
import websockets

from getstream.video.rtc.coordinator.chat_ws import StreamChatWS


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
async def test_connect_and_disconnect(mock_server):
    uri = f"ws://127.0.0.1:{mock_server['port']}/api/v2/connect"
    ws = StreamChatWS(
        api_key="k" * 32,
        api_secret="s" * 32,
        user_id="alice",
        uri=uri,
    )
    await ws.connect()
    assert ws.connected
    assert ws.connection_id == "conn-int"
    assert ws.user_id == "alice"

    await ws.disconnect()
    assert not ws.connected
