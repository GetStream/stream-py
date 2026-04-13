# WebSocket Client (`getstream.ws`)

General-purpose WebSocket client for consuming real-time events from Stream's coordinator API. Works with chat events, video call events, custom events, etc.

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

    async def on_call_event(event_type, event):
        print(f"{event_type}: {event}")
    ws.on_wildcard("call.**", on_call_event)

    # keep running until interrupted
    try:
        await asyncio.Event().wait()
    finally:
        await ws.disconnect()
        await client.aclose()

asyncio.run(main())
```

## Watching a video call

To receive events for a specific video call (custom events, participant joins/leaves, etc.), you must "watch" the call after connecting. The coordinator only delivers call-scoped events to connections that have subscribed.

**Important:** The watch request must use a **client-side token** (JWT with `user_id`), not the server admin token. The coordinator checks `IsClientSide()` and silently skips the subscription for server tokens.

```python
from getstream import AsyncStream
from getstream.utils import build_query_param

client = AsyncStream(api_key="...", api_secret="...")

# 1. Connect WS as the user
ws = await client.connect_ws(user_id="agent")

# 2. Watch the call with a client-side token
user_token = client.create_token("agent")
user_client = AsyncStream(
    api_key=client.api_key,
    api_secret=client.api_secret,
    base_url=client.base_url,
)
user_client.token = user_token
user_client.headers["authorization"] = user_token
user_client.client.headers["authorization"] = user_token

await user_client.video.get(
    "/api/v2/video/call/{type}/{id}",
    path_params={"type": "default", "id": "my-call-id"},
    query_params=build_query_param(connection_id=ws.connection_id),
)
await user_client.aclose()

# 3. Now call events arrive on the WS
@ws.on("custom")
def on_custom(event):
    print(event["custom"])
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

1. **URL construction** -- `base_url` scheme is swapped (`https` to `wss`, `http` to `ws`), path `/api/v2/connect` is appended, and `api_key`, `stream-auth-type=jwt`, `X-Stream-Client` are added as query params.

2. **Auth handshake** -- on WebSocket open, the client sends:
   ```json
   {"token": "<jwt>", "user_details": {"id": "alice", ...}}
   ```
   Server must respond with `connection.ok`. Any other response type (including `connection.error`) raises `StreamWSAuthError`.

3. **Background tasks** -- after auth, two async tasks start:
   - **Reader loop**: reads messages, parses JSON, emits events by their `type` field. Uses a `ws_id` counter to ignore stale messages from old connections during reconnect.
   - **Heartbeat loop**: sends `[{"type": "health.check", "client_id": "<connection_id>"}]` (array-wrapped per protocol) every 25s (configurable). If no message is received for 35s (configurable), triggers reconnect.

4. **Disconnect** -- cancels all background tasks (reader, heartbeat, reconnect), closes the socket with code 1000.

### Reconnection

Triggered automatically when:
- The server closes the connection with a non-1000 code (code 1000 = intentional close, no reconnect).
- The heartbeat detects no messages within `healthcheck_timeout`.
- A WebSocket error occurs while sending a heartbeat.

Strategy:
- **Exponential backoff with jitter**: base 0.25s, doubles per attempt, capped at 5s, plus random jitter to prevent thundering herd.
- **Max retries**: 5 by default, then gives up and sets `connected = False`.
- **Token refresh**: if the server rejects with error code 40 (`TOKEN_EXPIRED`) and the token was auto-generated (not a static user-provided token), the cached token is cleared and a fresh JWT is generated for the next attempt. Static tokens are treated as non-refreshable.
- **ws_id guard**: each connection increments an internal counter. The reader loop exits if the counter changes, preventing stale messages from old connections being emitted after reconnect.

### Event listening

`StreamWS` extends `StreamAsyncIOEventEmitter` (pyee-based). Two ways to listen:

```python
# Exact event type (supports decorator syntax via pyee)
@ws.on("message.new")
def handler(event):
    ...

# Wildcard patterns (direct call)
ws.on_wildcard("message.*", handler)     # single level: message.new, message.updated
ws.on_wildcard("call.**", handler)       # multi level: call.created, call.member.added
ws.on_wildcard("*", handler)             # all events

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
| `token` | auto-generated | Pre-generated JWT (skips auto-generation, treated as static/non-refreshable) |
| `user_agent` | `stream-python-client-{VERSION}` | Client identifier |
| `healthcheck_interval` | `25.0` | Seconds between heartbeat pings |
| `healthcheck_timeout` | `35.0` | Seconds of silence before reconnect |
| `max_retries` | `5` | Max reconnect attempts before giving up |
| `backoff_base` | `0.25` | Initial backoff delay in seconds |
| `backoff_max` | `5.0` | Maximum backoff delay in seconds |

Note: `connect_ws()` kwargs override the defaults from `AsyncStream` (e.g. you can pass a different `base_url`).

## Testing

### Unit tests (no credentials needed)

```
uv run pytest tests/ws/ --timeout=10
```

Tests use a local mock WebSocket server (`websockets.serve` on `127.0.0.1:0`) and cover:
- Instantiation and URL construction
- Auth handshake (success, failure, and unexpected response types)
- Event dispatch to typed and wildcard listeners
- Heartbeat message sending (array format)
- Auto-reconnect on server disconnect (non-1000 close codes)
- No reconnect on intentional close (code 1000)
- Token refresh on error code 40
- Static token protection (no refresh for user-provided tokens)
- ws_id stale message guard
- `AsyncStream.connect_ws()` integration and `aclose()` cleanup

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
- **Call watching requires manual setup** -- receiving call-scoped events requires a separate REST call with a client-side token (see "Watching a video call" above). This could be wrapped in a helper method in the future.
