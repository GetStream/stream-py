# Moderation

This guide shows how to migrate moderation code from `stream-chat` to `getstream`.

## Add Moderators

**Before (stream-chat):**

```python
from stream_chat import StreamChat

client = StreamChat(api_key="your-api-key", api_secret="your-api-secret")
channel = client.channel("messaging", "general")
channel.add_moderators(["user-1", "user-2"])
```

**After (getstream):**

```python
from getstream import Stream

client = Stream(api_key="your-api-key", api_secret="your-api-secret")
channel = client.chat.channel("messaging", "general")
response = channel.update(add_moderators=["user-1", "user-2"])
```

**Key changes:**
- No dedicated `add_moderators()` method; use `channel.update(add_moderators=[...])` instead
- Channel accessed via `client.chat.channel()`

## Demote Moderators

**Before (stream-chat):**

```python
from stream_chat import StreamChat

client = StreamChat(api_key="your-api-key", api_secret="your-api-secret")
channel = client.channel("messaging", "general")
channel.demote_moderators(["user-1"])
```

**After (getstream):**

```python
from getstream import Stream

client = Stream(api_key="your-api-key", api_secret="your-api-secret")
channel = client.chat.channel("messaging", "general")
response = channel.update(demote_moderators=["user-1"])
```

**Key changes:**
- No dedicated `demote_moderators()` method; use `channel.update(demote_moderators=[...])` instead

## Ban User (App-Level)

**Before (stream-chat):**

```python
from stream_chat import StreamChat

client = StreamChat(api_key="your-api-key", api_secret="your-api-secret")
client.ban_user(target_id="bad-user", user_id="admin", reason="Spam", timeout=3600)
```

**After (getstream):**

```python
from getstream import Stream

client = Stream(api_key="your-api-key", api_secret="your-api-secret")
response = client.moderation.ban(
    target_user_id="bad-user",
    banned_by_id="admin",
    reason="Spam",
    timeout=3600,
)
```

**Key changes:**
- Moderation methods moved to `client.moderation` sub-client
- `target_id` renamed to `target_user_id`
- `user_id` renamed to `banned_by_id`

## Ban User (Channel-Level)

**Before (stream-chat):**

```python
from stream_chat import StreamChat

client = StreamChat(api_key="your-api-key", api_secret="your-api-secret")
channel = client.channel("messaging", "general")
channel.ban_user(target_id="bad-user", user_id="admin", reason="Offensive")
```

**After (getstream):**

```python
from getstream import Stream

client = Stream(api_key="your-api-key", api_secret="your-api-secret")
response = client.moderation.ban(
    target_user_id="bad-user",
    banned_by_id="admin",
    reason="Offensive",
    channel_cid="messaging:general",
)
```

**Key changes:**
- Channel-level bans use `channel_cid` (format: `type:id`) on the moderation sub-client
- No separate channel-level ban method; same `ban()` with a `channel_cid` parameter

## Unban User

**Before (stream-chat):**

```python
from stream_chat import StreamChat

client = StreamChat(api_key="your-api-key", api_secret="your-api-secret")
client.unban_user(target_id="bad-user")
```

**After (getstream):**

```python
from getstream import Stream

client = Stream(api_key="your-api-key", api_secret="your-api-secret")
response = client.moderation.unban(
    target_user_id="bad-user",
    unbanned_by_id="admin",
)
```

**Key changes:**
- Called on `client.moderation` sub-client
- `target_id` renamed to `target_user_id`
- Requires `unbanned_by_id`

## Shadow Ban

**Before (stream-chat):**

```python
from stream_chat import StreamChat

client = StreamChat(api_key="your-api-key", api_secret="your-api-secret")
client.shadow_ban(target_id="user-1", user_id="admin")
```

**After (getstream):**

```python
from getstream import Stream

client = Stream(api_key="your-api-key", api_secret="your-api-secret")
response = client.moderation.ban(
    target_user_id="user-1",
    banned_by_id="admin",
    shadow=True,
)
```

**Key changes:**
- No dedicated `shadow_ban()` method; use `ban()` with `shadow=True`
- Remove shadow ban by calling `unban()` (same as a regular unban)

## Mute User

**Before (stream-chat):**

```python
from stream_chat import StreamChat

client = StreamChat(api_key="your-api-key", api_secret="your-api-secret")
client.mute_user(target_id="user-1", user_id="admin")
```

**After (getstream):**

```python
from getstream import Stream

client = Stream(api_key="your-api-key", api_secret="your-api-secret")
response = client.moderation.mute(
    target_ids=["user-1"],
    user_id="admin",
)
```

**Key changes:**
- Called on `client.moderation` sub-client
- `target_id` becomes `target_ids` (always a list, enabling batch mute)

## Unmute User

**Before (stream-chat):**

```python
from stream_chat import StreamChat

client = StreamChat(api_key="your-api-key", api_secret="your-api-secret")
client.unmute_user(target_id="user-1", user_id="admin")
```

**After (getstream):**

```python
from getstream import Stream

client = Stream(api_key="your-api-key", api_secret="your-api-secret")
response = client.moderation.unmute(
    target_ids=["user-1"],
    user_id="admin",
)
```

**Key changes:**
- Called on `client.moderation` sub-client
- `target_id` becomes `target_ids` (always a list)

## Summary: Method Mapping

| Use Case | stream-chat | getstream |
|----------|------------|-----------|
| Add moderators | `channel.add_moderators([...])` | `channel.update(add_moderators=[...])` |
| Demote moderators | `channel.demote_moderators([...])` | `channel.update(demote_moderators=[...])` |
| Ban (app-level) | `client.ban_user(target_id, user_id)` | `client.moderation.ban(target_user_id, banned_by_id)` |
| Ban (channel) | `channel.ban_user(target_id, user_id)` | `client.moderation.ban(..., channel_cid="type:id")` |
| Unban | `client.unban_user(target_id)` | `client.moderation.unban(target_user_id, unbanned_by_id)` |
| Shadow ban | `client.shadow_ban(target_id, user_id)` | `client.moderation.ban(..., shadow=True)` |
| Mute | `client.mute_user(target_id, user_id)` | `client.moderation.mute(target_ids=[...], user_id)` |
| Unmute | `client.unmute_user(target_id, user_id)` | `client.moderation.unmute(target_ids=[...], user_id)` |
