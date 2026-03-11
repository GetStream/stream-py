# Migrating from stream-chat to getstream

## Why Migrate?

- `getstream` is the actively developed, long-term-supported SDK
- Covers Chat, Video, Moderation, and Feeds in a single package
- Strongly typed models generated from the official OpenAPI spec
- `stream-chat` will enter maintenance mode (critical fixes only)

## Key Differences

| Aspect | stream-chat | getstream |
|--------|------------|-----------|
| Package | `pip install stream-chat` | `pip install getstream` |
| Import | `from stream_chat import StreamChat` | `from getstream import Stream` |
| Client init | `StreamChat(api_key, api_secret)` | `Stream(api_key, api_secret)` |
| Sub-clients | All methods on one client | `client.chat`, `client.moderation`, `client.video` |
| Channel access | `client.channel(type, id)` | `client.chat.channel(type, id)` |
| Models | Plain dicts | Typed dataclass models (`UserRequest`, `MessageRequest`, etc.) |
| Custom fields | Top-level dict keys | Nested in `custom` dict |
| Response access | Dict keys (`response["users"]`) | Typed properties (`response.data.users`) |
| Env vars | `STREAM_CHAT_TIMEOUT` | `STREAM_API_KEY`, `STREAM_API_SECRET`, `STREAM_TIMEOUT` |

## Quick Example

**Before:**

```python
from stream_chat import StreamChat

client = StreamChat(api_key="key", api_secret="secret")
client.upsert_user({"id": "user-1", "name": "Alice"})
channel = client.channel("messaging", "general")
channel.create("user-1")
channel.send_message({"text": "Hello!"}, user_id="user-1")
```

**After:**

```python
from getstream import Stream
from getstream.models import UserRequest, MessageRequest, ChannelInput

client = Stream(api_key="key", api_secret="secret")
client.upsert_users(UserRequest(id="user-1", name="Alice"))
channel = client.chat.channel("messaging", "general")
channel.get_or_create(data=ChannelInput(created_by_id="user-1"))
channel.send_message(message=MessageRequest(text="Hello!", user_id="user-1"))
```

## Migration Guides by Topic

| # | Topic | File |
|---|-------|------|
| 1 | [Setup and Authentication](01-setup-and-auth.md) | Client init, tokens |
| 2 | [Users](02-users.md) | Upsert, query, update, delete |
| 3 | [Channels](03-channels.md) | Create, query, members, update |
| 4 | [Messages and Reactions](04-messages-and-reactions.md) | Send, reply, react |
| 5 | [Moderation](05-moderation.md) | Ban, mute, moderators |
| 6 | [Devices](06-devices.md) | Push device management |

## Notes

- `stream-chat` is not going away. Your existing integration will keep working.
- The new SDK uses typed dataclass models for all request and response objects.
- If you find a use case missing from this guide, please open an issue.
