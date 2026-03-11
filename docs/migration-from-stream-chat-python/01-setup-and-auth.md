# Setup and Authentication

This guide shows how to migrate setup and authentication code from `stream-chat` to `getstream`.

## Installation

**Before (stream-chat):**

```bash
pip install stream-chat
```

**After (getstream):**

```bash
pip install getstream
```

## Client Initialization

**Before (stream-chat):**

```python
from stream_chat import StreamChat

client = StreamChat(api_key="your-api-key", api_secret="your-api-secret")
```

**After (getstream):**

```python
from getstream import Stream

client = Stream(api_key="your-api-key", api_secret="your-api-secret")
```

**Key changes:**
- Import changes from `stream_chat.StreamChat` to `getstream.Stream`
- The new SDK auto-loads `STREAM_API_KEY` and `STREAM_API_SECRET` from the environment or a `.env` file, so you can also initialize with `Stream()`

## Async Client

**Before (stream-chat):**

```python
from stream_chat import StreamChatAsync

async with StreamChatAsync(api_key="your-api-key", api_secret="your-api-secret") as client:
    response = await client.get_app_settings()
```

**After (getstream):**

```python
from getstream import Stream

client = Stream(api_key="your-api-key", api_secret="your-api-secret")
async_client = client.as_async()
```

**Key changes:**
- No separate `StreamChatAsync` class; call `client.as_async()` on the sync client instead
- The async client has full parity with the sync client

## Creating a User Token

**Before (stream-chat):**

```python
from stream_chat import StreamChat

client = StreamChat(api_key="your-api-key", api_secret="your-api-secret")
token = client.create_token("user-1", expiration=3600)
```

**After (getstream):**

```python
from getstream import Stream

client = Stream(api_key="your-api-key", api_secret="your-api-secret")
token = client.create_token(user_id="user-1", expiration=3600)
```

**Key changes:**
- Method name is the same (`create_token`), but uses explicit keyword arguments

## Environment Variables

**Before (stream-chat):**

| Variable | Purpose |
|----------|---------|
| `STREAM_CHAT_TIMEOUT` | Request timeout |
| `STREAM_CHAT_URL` | Custom base URL |

**After (getstream):**

| Variable | Purpose |
|----------|---------|
| `STREAM_API_KEY` | API key (auto-loaded) |
| `STREAM_API_SECRET` | API secret (auto-loaded) |
| `STREAM_BASE_URL` | Custom base URL |
| `STREAM_TIMEOUT` | Request timeout |

## Sub-clients

The new SDK organizes methods into product-specific sub-clients accessed from the main client:

| Sub-client | Access | Description |
|------------|--------|-------------|
| Chat | `client.chat` | Channels, messages, reactions |
| Video | `client.video` | Calls, call types |
| Moderation | `client.moderation` | Ban, mute, flag |
| Feeds | `client.feeds` | Activity feeds (sync only) |
