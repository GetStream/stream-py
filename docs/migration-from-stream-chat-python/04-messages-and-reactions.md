# Messages and Reactions

This guide shows how to migrate message and reaction code from `stream-chat` to `getstream`.

## Send a Message

**Before (stream-chat):**

```python
from stream_chat import StreamChat

client = StreamChat(api_key="your-api-key", api_secret="your-api-secret")
channel = client.channel("messaging", "general")
response = channel.send_message({"text": "Hello world"}, user_id="user-1")
```

**After (getstream):**

```python
from getstream import Stream
from getstream.models import MessageRequest

client = Stream(api_key="your-api-key", api_secret="your-api-secret")
channel = client.chat.channel("messaging", "general")
response = channel.send_message(
    message=MessageRequest(text="Hello world", user_id="user-1")
)
```

**Key changes:**
- Message content and `user_id` are combined in a `MessageRequest` object
- `user_id` moves inside the request model instead of being a separate argument

## Send a Message with Options

**Before (stream-chat):**

```python
from stream_chat import StreamChat

client = StreamChat(api_key="your-api-key", api_secret="your-api-secret")
channel = client.channel("messaging", "general")
response = channel.send_message(
    {"text": "Silent notification", "custom_field": "value"},
    user_id="user-1",
    skip_push=True,
)
```

**After (getstream):**

```python
from getstream import Stream
from getstream.models import MessageRequest

client = Stream(api_key="your-api-key", api_secret="your-api-secret")
channel = client.chat.channel("messaging", "general")
response = channel.send_message(
    message=MessageRequest(
        text="Silent notification",
        user_id="user-1",
        custom={"custom_field": "value"},
    ),
    skip_push=True,
)
```

**Key changes:**
- Custom fields go in the `custom` dict on `MessageRequest`
- Send options like `skip_push` remain as keyword arguments on `send_message()`

## Send a Thread Reply

**Before (stream-chat):**

```python
from stream_chat import StreamChat

client = StreamChat(api_key="your-api-key", api_secret="your-api-secret")
channel = client.channel("messaging", "general")
response = channel.send_message(
    {"text": "Reply text", "parent_id": "parent-msg-id"},
    user_id="user-1",
)
```

**After (getstream):**

```python
from getstream import Stream
from getstream.models import MessageRequest

client = Stream(api_key="your-api-key", api_secret="your-api-secret")
channel = client.chat.channel("messaging", "general")
response = channel.send_message(
    message=MessageRequest(
        text="Reply text",
        user_id="user-1",
        parent_id="parent-msg-id",
        show_in_channel=False,
    )
)
```

**Key changes:**
- `parent_id` is a named field on `MessageRequest` instead of a dict key
- `show_in_channel` can be set explicitly on the request

## Get a Message

**Before (stream-chat):**

```python
from stream_chat import StreamChat

client = StreamChat(api_key="your-api-key", api_secret="your-api-secret")
response = client.get_message("msg-123")
```

**After (getstream):**

```python
from getstream import Stream

client = Stream(api_key="your-api-key", api_secret="your-api-secret")
response = client.chat.get_message(id="msg-123")
```

**Key changes:**
- Called on `client.chat` sub-client instead of `client` directly

## Update a Message

**Before (stream-chat):**

```python
from stream_chat import StreamChat

client = StreamChat(api_key="your-api-key", api_secret="your-api-secret")
response = client.update_message({
    "id": "msg-123",
    "text": "Updated text",
    "user": {"id": "user-1"},
})
```

**After (getstream):**

```python
from getstream import Stream
from getstream.models import MessageRequest

client = Stream(api_key="your-api-key", api_secret="your-api-secret")
response = client.chat.update_message(
    id="msg-123",
    message=MessageRequest(text="Updated text"),
)
```

**Key changes:**
- Message ID is a separate `id` parameter, not part of the message dict
- No need to embed `user` inside the message; the SDK handles authentication

## Partial Update a Message

**Before (stream-chat):**

```python
from stream_chat import StreamChat

client = StreamChat(api_key="your-api-key", api_secret="your-api-secret")
response = client.update_message_partial(
    message_id="msg-123",
    updates={"set": {"text": "Edited text"}, "unset": ["old_field"]},
    user_id="user-1",
)
```

**After (getstream):**

```python
from getstream import Stream

client = Stream(api_key="your-api-key", api_secret="your-api-secret")
response = client.chat.update_message_partial(
    id="msg-123",
    set={"text": "Edited text"},
    unset=["old_field"],
)
```

**Key changes:**
- `set` and `unset` are top-level keyword arguments instead of a nested `updates` dict
- `message_id` renamed to `id`

## Delete a Message

**Before (stream-chat):**

```python
from stream_chat import StreamChat

client = StreamChat(api_key="your-api-key", api_secret="your-api-secret")
response = client.delete_message("msg-123")
```

**After (getstream):**

```python
from getstream import Stream

client = Stream(api_key="your-api-key", api_secret="your-api-secret")
response = client.chat.delete_message(id="msg-123", hard=False)
```

**Key changes:**
- Called on `client.chat` sub-client
- `hard` parameter is explicit (defaults to soft delete)

## Send a Reaction

**Before (stream-chat):**

```python
from stream_chat import StreamChat

client = StreamChat(api_key="your-api-key", api_secret="your-api-secret")
channel = client.channel("messaging", "general")
response = channel.send_reaction(
    message_id="msg-123",
    reaction={"type": "love", "count": 42},
    user_id="user-1",
)
```

**After (getstream):**

```python
from getstream import Stream
from getstream.models import ReactionRequest

client = Stream(api_key="your-api-key", api_secret="your-api-secret")
response = client.chat.send_reaction(
    id="msg-123",
    reaction=ReactionRequest(type="love", score=42),
    enforce_unique=False,
)
```

**Key changes:**
- Called on `client.chat` sub-client instead of the channel object
- Uses `ReactionRequest` instead of a plain dict
- `count` field renamed to `score`
- `user_id` can be passed inside `ReactionRequest(user_id=...)` when needed (e.g. server-side reactions on behalf of a user)
- `enforce_unique` controls whether a user can add multiple reactions of the same type (when `True`, the new reaction replaces any existing one of the same type by that user)

## List Reactions

**Before (stream-chat):**

```python
from stream_chat import StreamChat

client = StreamChat(api_key="your-api-key", api_secret="your-api-secret")
channel = client.channel("messaging", "general")
response = channel.get_reactions("msg-123", limit=10, offset=0)
```

**After (getstream):**

```python
from getstream import Stream

client = Stream(api_key="your-api-key", api_secret="your-api-secret")
response = client.chat.get_reactions(id="msg-123", limit=10, offset=0)
```

**Key changes:**
- Called on `client.chat` sub-client instead of the channel object
- Message ID passed as `id` keyword argument

## Delete a Reaction

**Before (stream-chat):**

```python
from stream_chat import StreamChat

client = StreamChat(api_key="your-api-key", api_secret="your-api-secret")
channel = client.channel("messaging", "general")
response = channel.delete_reaction("msg-123", reaction_type="love", user_id="user-1")
```

**After (getstream):**

```python
from getstream import Stream

client = Stream(api_key="your-api-key", api_secret="your-api-secret")
response = client.chat.delete_reaction(
    id="msg-123",
    type="love",
    user_id="user-1",
)
```

**Key changes:**
- Called on `client.chat` sub-client instead of the channel object
- `reaction_type` renamed to `type`
