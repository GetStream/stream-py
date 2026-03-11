# Channels

This guide shows how to migrate channel management code from `stream-chat` to `getstream`.

## Create a Channel (with ID)

**Before (stream-chat):**

```python
from stream_chat import StreamChat

client = StreamChat(api_key="your-api-key", api_secret="your-api-secret")
channel = client.channel("messaging", "general")
response = channel.create("user-1")
```

**After (getstream):**

```python
from getstream import Stream
from getstream.models import ChannelInput

client = Stream(api_key="your-api-key", api_secret="your-api-secret")
channel = client.chat.channel("messaging", "general")
response = channel.get_or_create(
    data=ChannelInput(created_by_id="user-1")
)
```

**Key changes:**
- Channel is accessed via `client.chat.channel()` instead of `client.channel()`
- `channel.create(user_id)` becomes `channel.get_or_create(data=ChannelInput(created_by_id=user_id))`

## Create a Distinct Channel (by Members)

**Before (stream-chat):**

```python
from stream_chat import StreamChat

client = StreamChat(api_key="your-api-key", api_secret="your-api-secret")
channel = client.channel("messaging", data={"members": ["user-1", "user-2"]})
channel.create("user-1")
```

**After (getstream):**

```python
from getstream import Stream
from getstream.models import ChannelInput, ChannelMemberRequest

client = Stream(api_key="your-api-key", api_secret="your-api-secret")
response = client.chat.get_or_create_distinct_channel(
    type="messaging",
    data=ChannelInput(
        created_by_id="user-1",
        members=[
            ChannelMemberRequest(user_id="user-1"),
            ChannelMemberRequest(user_id="user-2"),
        ],
    ),
)
```

**Key changes:**
- Uses `client.chat.get_or_create_distinct_channel()` instead of `client.channel()` with no ID
- Members use `ChannelMemberRequest` objects instead of plain strings
- Member list goes inside `ChannelInput` rather than a data dict

## Query Channels

**Before (stream-chat):**

```python
from stream_chat import StreamChat

client = StreamChat(api_key="your-api-key", api_secret="your-api-secret")
response = client.query_channels(
    filter_conditions={"members": {"$in": ["user-1"]}},
    sort=[{"field": "last_message_at", "direction": -1}],
    limit=20,
)
```

**After (getstream):**

```python
from getstream import Stream
from getstream.models import SortParamRequest

client = Stream(api_key="your-api-key", api_secret="your-api-secret")
response = client.chat.query_channels(
    filter_conditions={"members": {"$in": ["user-1"]}},
    sort=[SortParamRequest(field="last_message_at", direction=-1)],
    limit=20,
)
```

**Key changes:**
- Called on `client.chat` sub-client instead of `client` directly
- Sort uses `SortParamRequest` objects instead of plain dicts

## Add Members

**Before (stream-chat):**

```python
from stream_chat import StreamChat

client = StreamChat(api_key="your-api-key", api_secret="your-api-secret")
channel = client.channel("messaging", "general")
channel.add_members(["user-3", "user-4"])
```

**After (getstream):**

```python
from getstream import Stream
from getstream.models import ChannelMemberRequest

client = Stream(api_key="your-api-key", api_secret="your-api-secret")
channel = client.chat.channel("messaging", "general")
response = channel.update(
    add_members=[
        ChannelMemberRequest(user_id="user-3"),
        ChannelMemberRequest(user_id="user-4"),
    ]
)
```

**Key changes:**
- No dedicated `add_members()` method; use `channel.update(add_members=[...])` instead
- Members are `ChannelMemberRequest` objects instead of plain strings

## Remove Members

**Before (stream-chat):**

```python
from stream_chat import StreamChat

client = StreamChat(api_key="your-api-key", api_secret="your-api-secret")
channel = client.channel("messaging", "general")
channel.remove_members(["user-3"])
```

**After (getstream):**

```python
from getstream import Stream

client = Stream(api_key="your-api-key", api_secret="your-api-secret")
channel = client.chat.channel("messaging", "general")
response = channel.update(remove_members=["user-3"])
```

**Key changes:**
- No dedicated `remove_members()` method; use `channel.update(remove_members=[...])` instead

## Full Channel Update

**Before (stream-chat):**

```python
from stream_chat import StreamChat

client = StreamChat(api_key="your-api-key", api_secret="your-api-secret")
channel = client.channel("messaging", "general")
channel.update({"color": "blue", "name": "General Chat"})
```

**After (getstream):**

```python
from getstream import Stream
from getstream.models import ChannelInputRequest

client = Stream(api_key="your-api-key", api_secret="your-api-secret")
channel = client.chat.channel("messaging", "general")
response = channel.update(
    data=ChannelInputRequest(custom={"color": "blue", "name": "General Chat"})
)
```

**Key changes:**
- Channel data passed as `ChannelInputRequest` via the `data` keyword instead of a plain dict
- Custom fields go in the `custom` dict

## Partial Channel Update

**Before (stream-chat):**

```python
from stream_chat import StreamChat

client = StreamChat(api_key="your-api-key", api_secret="your-api-secret")
channel = client.channel("messaging", "general")
channel.update_partial(to_set={"color": "red"}, to_unset=["old_field"])
```

**After (getstream):**

```python
from getstream import Stream

client = Stream(api_key="your-api-key", api_secret="your-api-secret")
channel = client.chat.channel("messaging", "general")
response = channel.update_channel_partial(
    set={"color": "red"},
    unset=["old_field"],
)
```

**Key changes:**
- Method renamed from `update_partial()` to `update_channel_partial()`
- Parameters renamed from `to_set`/`to_unset` to `set`/`unset`

## Delete Channel

**Before (stream-chat):**

```python
from stream_chat import StreamChat

client = StreamChat(api_key="your-api-key", api_secret="your-api-secret")
channel = client.channel("messaging", "general")
channel.delete()
```

**After (getstream):**

```python
from getstream import Stream

client = Stream(api_key="your-api-key", api_secret="your-api-secret")
channel = client.chat.channel("messaging", "general")
response = channel.delete(hard_delete=False)
```

**Key changes:**
- `hard_delete` parameter is explicit (defaults to `False` for soft delete)

## Delete Multiple Channels

**Before (stream-chat):**

```python
from stream_chat import StreamChat

client = StreamChat(api_key="your-api-key", api_secret="your-api-secret")
response = client.delete_channels(
    ["messaging:channel1", "team:channel2"],
    hard_delete=True,
)
```

**After (getstream):**

```python
from getstream import Stream

client = Stream(api_key="your-api-key", api_secret="your-api-secret")
response = client.chat.delete_channels(
    cids=["messaging:channel1", "team:channel2"],
    hard_delete=True,
)
```

**Key changes:**
- Called on `client.chat` sub-client
- CIDs passed via `cids` keyword argument
