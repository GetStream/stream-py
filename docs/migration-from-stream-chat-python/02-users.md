# Users

This guide shows how to migrate user management code from `stream-chat` to `getstream`.

## Upsert a Single User

**Before (stream-chat):**

```python
from stream_chat import StreamChat

client = StreamChat(api_key="your-api-key", api_secret="your-api-secret")
response = client.upsert_user({"id": "user-1", "name": "Alice", "role": "admin"})
```

**After (getstream):**

```python
from getstream import Stream
from getstream.models import UserRequest

client = Stream(api_key="your-api-key", api_secret="your-api-secret")
response = client.upsert_users(
    UserRequest(id="user-1", name="Alice", role="admin")
)
```

**Key changes:**
- Plain dicts replaced by typed `UserRequest` objects
- Method is `upsert_users()` (accepts one or more `UserRequest` arguments)

## Upsert Multiple Users

**Before (stream-chat):**

```python
from stream_chat import StreamChat

client = StreamChat(api_key="your-api-key", api_secret="your-api-secret")
response = client.upsert_users([
    {"id": "user-1", "name": "Alice"},
    {"id": "user-2", "name": "Bob"},
])
```

**After (getstream):**

```python
from getstream import Stream
from getstream.models import UserRequest

client = Stream(api_key="your-api-key", api_secret="your-api-secret")
response = client.upsert_users(
    UserRequest(id="user-1", name="Alice"),
    UserRequest(id="user-2", name="Bob"),
)
```

**Key changes:**
- Pass multiple `UserRequest` arguments instead of a list of dicts

## Custom Fields

**Before (stream-chat):**

```python
from stream_chat import StreamChat

client = StreamChat(api_key="your-api-key", api_secret="your-api-secret")
response = client.upsert_user({
    "id": "user-1",
    "name": "Alice",
    "favorite_color": "blue",
    "premium": True,
})
```

**After (getstream):**

```python
from getstream import Stream
from getstream.models import UserRequest

client = Stream(api_key="your-api-key", api_secret="your-api-secret")
response = client.upsert_users(
    UserRequest(
        id="user-1",
        name="Alice",
        custom={"favorite_color": "blue", "premium": True},
    )
)
```

**Key changes:**
- Custom fields go in the `custom` dict instead of being mixed with standard fields at the top level

## Query Users

**Before (stream-chat):**

```python
from stream_chat import StreamChat

client = StreamChat(api_key="your-api-key", api_secret="your-api-secret")
response = client.query_users(
    filter_conditions={"role": {"$eq": "admin"}},
    sort=[{"field": "created_at", "direction": -1}],
    limit=10,
)
```

**After (getstream):**

```python
from getstream import Stream
from getstream.models import QueryUsersPayload, SortParamRequest

client = Stream(api_key="your-api-key", api_secret="your-api-secret")
response = client.query_users(
    QueryUsersPayload(
        filter_conditions={"role": {"$eq": "admin"}},
        sort=[SortParamRequest(field="created_at", direction=-1)],
        limit=10,
    )
)
```

**Key changes:**
- Filter and sort are wrapped in `QueryUsersPayload` and `SortParamRequest` models
- Sort uses `SortParamRequest` objects instead of plain dicts

## Partial Update User

**Before (stream-chat):**

```python
from stream_chat import StreamChat

client = StreamChat(api_key="your-api-key", api_secret="your-api-secret")
response = client.update_user_partial({
    "id": "user-1",
    "set": {"name": "Alice Updated", "status": "online"},
    "unset": ["old_field"],
})
```

**After (getstream):**

```python
from getstream import Stream
from getstream.models import UpdateUserPartialRequest

client = Stream(api_key="your-api-key", api_secret="your-api-secret")
response = client.update_users_partial(
    users=[
        UpdateUserPartialRequest(
            id="user-1",
            set={"name": "Alice Updated", "status": "online"},
            unset=["old_field"],
        )
    ]
)
```

**Key changes:**
- Method renamed from `update_user_partial()` to `update_users_partial()`
- Takes a list of `UpdateUserPartialRequest` objects via the `users` parameter

## Deactivate User

**Before (stream-chat):**

```python
from stream_chat import StreamChat

client = StreamChat(api_key="your-api-key", api_secret="your-api-secret")
response = client.deactivate_user("user-1")
```

**After (getstream):**

```python
from getstream import Stream

client = Stream(api_key="your-api-key", api_secret="your-api-secret")
response = client.deactivate_user(
    user_id="user-1",
    mark_messages_deleted=False,
)
```

**Key changes:**
- Uses explicit keyword arguments instead of positional string

## Deactivate Multiple Users

**Before (stream-chat):**

```python
from stream_chat import StreamChat

client = StreamChat(api_key="your-api-key", api_secret="your-api-secret")
response = client.deactivate_users(["user-1", "user-2"])
```

**After (getstream):**

```python
from getstream import Stream

client = Stream(api_key="your-api-key", api_secret="your-api-secret")
response = client.deactivate_users(user_ids=["user-1", "user-2"])
```

**Key changes:**
- Uses `user_ids` keyword argument instead of positional list

## Delete Users

**Before (stream-chat):**

```python
from stream_chat import StreamChat

client = StreamChat(api_key="your-api-key", api_secret="your-api-secret")
response = client.delete_users(
    ["user-1", "user-2"],
    delete_type="hard",
    conversations="hard",
    messages="hard",
)
```

**After (getstream):**

```python
from getstream import Stream

client = Stream(api_key="your-api-key", api_secret="your-api-secret")
response = client.delete_users(
    user_ids=["user-1", "user-2"],
    user="hard",
    conversations="hard",
    messages="hard",
)
```

**Key changes:**
- Uses `user_ids` keyword argument instead of positional list
- `delete_type` parameter renamed to `user`
