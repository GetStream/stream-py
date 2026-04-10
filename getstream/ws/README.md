# WebSocket Client (`getstream.ws`)

General-purpose WebSocket client for consuming real-time events from Stream's coordinator API. Works with chat events, video events, custom events, etc.

## Install

```
pip install getstream[ws]
```

## Quick start

```python
import asyncio
from getstream import AsyncStream

async def main():
    client = AsyncStream(api_key="your-key", api_secret="your-secret")

    ws = await client.connect_ws(
        user_id="alice",
        user_details={"id": "alice", "name": "Alice"},
    )

    @ws.on("message.new")
    async def on_message(event):
        print(f"New message in {event['cid']}: {event['message']['text']}")

    @ws.on_wildcard("call.**")
    async def on_call_event(event_type, event):
        print(f"{event_type}: {event}")

    # keep running until interrupted
    try:
        await asyncio.Event().wait()
    finally:
        await ws.disconnect()
        await client.aclose()

asyncio.run(main())
```

## Standalone usage (without AsyncStream)

```python
from getstream.ws import StreamWS

ws = StreamWS(
    api_key="your-key",
    api_secret="your-secret",
    user_id="alice",
    user_details={"id": "alice", "name": "Alice"},
)
await ws.connect()
# ... register listeners, do work ...
await ws.disconnect()
```

## How it works

### Connection lifecycle

1. **URL construction** -- `base_url` scheme is swapped (`https` to `wss`, `http` to `ws`), path `/connect` is appended, and `api_key`, `stream-auth-type=jwt`, `X-Stream-Client` are added as query params.

2. **Auth handshake** -- on WebSocket open, the client sends:
   ```json
   {"token": "<jwt>", "user_details": {"id": "alice", ...}}
   ```
   Server responds with `connection.ok` (success) or `connection.error` (failure).

3. **Background tasks** -- after auth, two async tasks start:
   - **Reader loop**: reads messages, parses JSON, emits events by their `type` field.
   - **Heartbeat loop**: sends `{"type": "health.check", "client_id": "<connection_id>"}` every 25s (configurable). If no message is received for 35s (configurable), triggers reconnect.

4. **Disconnect** -- cancels background tasks, closes the socket with code 1000.

### Reconnection

Triggered automatically when:
- The server closes the connection unexpectedly.
- The heartbeat detects no messages within `healthcheck_timeout`.
- A WebSocket error occurs while sending a heartbeat.

Strategy:
- **Exponential backoff with jitter**: base 0.25s, doubles per attempt, capped at 5s, plus random jitter to prevent thundering herd.
- **Max retries**: 5 by default, then gives up and sets `connected = False`.
- **Token refresh**: if the server rejects with error code 40 (`TOKEN_EXPIRED`), the cached token is cleared and a fresh JWT is generated for the next attempt.

### Event listening

`StreamWS` extends `StreamAsyncIOEventEmitter` (pyee-based). Two ways to listen:

```python
# Exact event type
@ws.on("message.new")
def handler(event):
    ...

# Wildcard patterns
@ws.on_wildcard("message.*")     # single level: message.new, message.updated
def handler(event_type, event):
    ...

@ws.on_wildcard("call.**")      # multi level: call.created, call.member.added
def handler(event_type, event):
    ...

@ws.on_wildcard("*")            # all events
def handler(event_type, event):
    ...
```

Both sync and async handlers are supported.

## Configuration

All constructor params (also accepted as kwargs to `client.connect_ws()`):

| Param | Default | Description |
|-------|---------|-------------|
| `api_key` | required | Stream API key |
| `api_secret` | required | Stream API secret (used to generate JWT) |
| `user_id` | required | User ID to connect as |
| `user_details` | `{"id": user_id}` | User details sent during auth |
| `base_url` | `https://chat.stream-io-api.com` | Base API URL |
| `token` | auto-generated | Pre-generated JWT (skips auto-generation) |
| `user_agent` | `stream-python-client-{VERSION}` | Client identifier |
| `healthcheck_interval` | `25.0` | Seconds between heartbeat pings |
| `healthcheck_timeout` | `35.0` | Seconds of silence before reconnect |
| `max_retries` | `5` | Max reconnect attempts before giving up |
| `backoff_base` | `0.25` | Initial backoff delay in seconds |
| `backoff_max` | `5.0` | Maximum backoff delay in seconds |

## Testing

### Unit tests (no credentials needed)

```
uv run pytest tests/ws/ --timeout=10
```

Tests use a local mock WebSocket server (`websockets.serve` on `127.0.0.1:0`) and cover:
- Instantiation and URL construction
- Auth handshake (success and failure)
- Event dispatch to typed and wildcard listeners
- Heartbeat message sending
- Auto-reconnect on server disconnect
- Token refresh on error code 40
- `AsyncStream.connect_ws()` integration and `aclose()` cleanup

### Manual integration test (requires credentials)

```python
import asyncio
from getstream import AsyncStream

async def main():
    client = AsyncStream(api_key="...", api_secret="...")

    # Create a user first
    await client.upsert_users(UserRequest(id="test-ws-user"))

    # Connect WS as that user
    ws = await client.connect_ws(user_id="test-ws-user")

    received = []
    @ws.on_wildcard("*")
    def on_any(event_type, event):
        print(f"[{event_type}] {event}")
        received.append(event)

    # In another terminal or script, send a chat message via REST API
    # to a channel the user is a member of. Verify the event appears here.

    await asyncio.sleep(30)
    print(f"Received {len(received)} events")

    await ws.disconnect()
    await client.aclose()

asyncio.run(main())
```

### Debugging

Enable WebSocket-level debug logs:

```python
import logging
logging.getLogger("getstream.ws.client").setLevel(logging.DEBUG)
logging.getLogger("websockets.client").setLevel(logging.DEBUG)
```

## Architecture

```
getstream/ws/
  __init__.py       -- exports StreamWS, StreamWSAuthError
  client.py         -- StreamWS class (connection, auth, reader, heartbeat, reconnect)

getstream/stream.py -- AsyncStream.connect_ws() convenience method

Tests:
  tests/ws/
    test_ws_client.py        -- unit tests for StreamWS
    test_async_stream_ws.py  -- integration tests for AsyncStream.connect_ws()
```

Reference implementation: `stream-video-js/packages/client/src/coordinator/connection/connection.ts`

## Known limitations

- **Async only** -- WebSocket is inherently async. Sync users can call `stream.as_async()` to get an `AsyncStream`.
- **No `products` filter yet** -- the JS SDK sends `products: ["video"]` or `["chat"]` to filter events. This can be added to the auth payload when needed.
- **Single connection per `connect_ws()` call** -- each call creates a separate WS connection. No multiplexing.
