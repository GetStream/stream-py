# Devices

This guide shows how to migrate push device management code from `stream-chat` to `getstream`.

## Add a Device (APN)

**Before (stream-chat):**

```python
from stream_chat import StreamChat

client = StreamChat(api_key="your-api-key", api_secret="your-api-secret")
client.add_device(
    device_id="apn-device-token",
    push_provider="apn",
    user_id="user-1",
    push_provider_name="my-apn-provider",
)
```

**After (getstream):**

```python
from getstream import Stream

client = Stream(api_key="your-api-key", api_secret="your-api-secret")
response = client.create_device(
    id="apn-device-token",
    push_provider="apn",
    user_id="user-1",
    push_provider_name="my-apn-provider",
)
```

**Key changes:**
- `add_device()` renamed to `create_device()`
- `device_id` parameter renamed to `id`

## Add a Device (Firebase)

**Before (stream-chat):**

```python
from stream_chat import StreamChat

client = StreamChat(api_key="your-api-key", api_secret="your-api-secret")
client.add_device(
    device_id="fcm-registration-token",
    push_provider="firebase",
    user_id="user-1",
)
```

**After (getstream):**

```python
from getstream import Stream

client = Stream(api_key="your-api-key", api_secret="your-api-secret")
response = client.create_device(
    id="fcm-registration-token",
    push_provider="firebase",
    user_id="user-1",
)
```

**Key changes:**
- Same pattern: `add_device()` becomes `create_device()`, `device_id` becomes `id`

## Add a VoIP Device

**Before (stream-chat):**

The legacy SDK does not have explicit VoIP device support.

**After (getstream):**

```python
from getstream import Stream

client = Stream(api_key="your-api-key", api_secret="your-api-secret")
response = client.create_device(
    id="voip-device-token",
    push_provider="apn",
    user_id="user-1",
    voip_token=True,
)
```

**Key changes:**
- The new SDK adds `voip_token=True` for Apple VoIP push tokens

## List Devices

**Before (stream-chat):**

```python
from stream_chat import StreamChat

client = StreamChat(api_key="your-api-key", api_secret="your-api-secret")
response = client.get_devices("user-1")
devices = response["devices"]
```

**After (getstream):**

```python
from getstream import Stream

client = Stream(api_key="your-api-key", api_secret="your-api-secret")
response = client.list_devices(user_id="user-1")
devices = response.data.devices
```

**Key changes:**
- `get_devices()` renamed to `list_devices()`
- Response accessed via typed `response.data.devices` instead of dict key access

## Delete a Device

**Before (stream-chat):**

```python
from stream_chat import StreamChat

client = StreamChat(api_key="your-api-key", api_secret="your-api-secret")
client.delete_device(device_id="device-123", user_id="user-1")
```

**After (getstream):**

```python
from getstream import Stream

client = Stream(api_key="your-api-key", api_secret="your-api-secret")
response = client.delete_device(id="device-123", user_id="user-1")
```

**Key changes:**
- `device_id` parameter renamed to `id`

## Summary: Method Mapping

| Use Case | stream-chat | getstream |
|----------|------------|-----------|
| Add device | `client.add_device(device_id, push_provider, user_id)` | `client.create_device(id, push_provider, user_id)` |
| List devices | `client.get_devices(user_id)` | `client.list_devices(user_id)` |
| Delete device | `client.delete_device(device_id, user_id)` | `client.delete_device(id, user_id)` |
