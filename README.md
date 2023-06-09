# Stream Video Client Library

The Stream Client Library provides a simple way to interact with the Stream API for managing video and chat services. This Python library makes it easy to create, manage, and authenticate video calls and chat sessions programmatically.

## Features

- Video call creation and management
- Chat session creation and management
- Token generation for user authentication with support for roles and call IDs

## Installation

To install the Stream Client Library, run the following command:

```sh
pip install getstream
```

Replace `stream` with the actual package name you'll use when publishing your library.

## Usage

To get started, you need to import the `Stream` class from the library and create a new instance with your API key and secret:

```python
from getstream import Stream

client = Stream(api_key="your_api_key", api_secret="your_api_secret")
```

### Video Calls

To create a video call or retrieve an existing one, use the `client.video.call` method:

```python
import uuid

call = client.video.call(
    "livestream",
    uuid.uuid4(),
    data={
        "created_by_id": "admin-user",
        "settings_override": {
            "broadcasting": {
                "enabled": True,
                "hls": {
                    "enabled": True,
                    "quality_tracks": ["480p", "720p", "1080p"],
                },
            },
        },
    },
)

response = call.get_or_create()
print(response)
```

### Chat Sessions

To work with chat sessions, use the `client.chat` object and implement the desired chat methods in the `Chat` class:

```python
chat_instance = client.chat

# Implement and call chat-related methods with chat_instance
```

### User Authentication

To generate a JWT token for user authentication with role and call ID support, use the `client.create_token` method:

```python
token = client.create_token("admin-user", call_cids=[call.cid], role="admin")
```

### Cli for signing tokens

You can sign tokens by running the cli

```sh
poetry run create-token --api-key API_KEY --api-secret API_SECRET --user-id USER_ID [--expiration EXPIRATION]
```

Or you can use docker
First, build the image

```sh
docker build -t stream-py .
```

Then run the container

```sh
docker run -it --rm stream-py --api-key API_KEY --api-secret API_SECRET
```

Or use the published one 
```sh
docker run -it --rm ghcr.io/getstream/stream-py:main --api-key API_KEY --api-secret API_SECRET --user-id
```

## License

This project is licensed under the [MIT License](LICENSE).

## Contributing

Contributions are welcome! Please read the [contributing guidelines](CONTRIBUTING.md) to get started.
