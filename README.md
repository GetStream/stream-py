# Official Python SDK for [Stream](https://getstream.io/)

[![build](https://github.com/GetStream/stream-py/workflows/build/badge.svg)](https://github.com/GetStream/stream-chat-python/actions) [![PyPI version](https://badge.fury.io/py/getstream.svg)](http://badge.fury.io/py/getstream) ![PyPI - Python Version](https://img.shields.io/pypi/pyversions/getstream.svg)

## Features

- Video call creation and management
- Chat session creation and management
- Token generation for user authentication

## Installation

To install the Stream Client Library, run the following command:

```sh
pip install getstream
```

## Usage

To get started, you need to import the `Stream` class from the library and create a new instance with your API key and secret:

```python
from getstream import Stream

client = Stream(api_key="your_api_key", api_secret="your_api_secret")
```

### Users and Authentication

```python
# Create a user token to connect with a client-side SDK
token = client.create_token("jane")

# Ensure a user exists

```

### Video API - Calls

To create a video call, use the `client.video.call` method:

```python
import uuid

call = client.video.call(
    call_type = "livestream",
    call_id = uuid.uuid4())
)

response = call.create(
        data=CallRequest(
            created_by_id="admin-user",
            settings_override=CallSettingsRequest(
                broadcasting=BroadcastSettingsRequest(
                    enabled=True,
                    hls=HlssettingsRequest(
                        enabled=True,
                        quality_tracks=["480p", "720p", "1080p"],
                    ),
                ),
            ),
        ),
    )
print(response)
```

### App configuration

```python
# Video: update settings for a call type

# Chat: update settings for a channel type
```


### Chat API - Channels

To work with chat sessions, use the `client.chat` object and implement the desired chat methods in the `Chat` class:

```python
chat_instance = client.chat

# Implement and call chat-related methods with chat_instance
```

## Development

We use poetry to manage dependencies and run tests. It's a package manager for Python that allows you to declare the libraries your project depends on and manage them.
To install the development dependencies, run the following command:

```sh
poetry install
```

To activate the virtual environment, run the following command:

```sh
poetry shell
```

To run tests, create a `.env` using the `.env.example` and adjust it to have valid API credentials 
```sh
poetry run pytest tests/ getstream/
```

Before pushing changes make sure to run the linter:

```sh
poetry run ruff check tests getstream --fix
```

## License

This project is licensed under the [MIT License](LICENSE).

## Contributing

Contributions are welcome! Please read the [contributing guidelines](CONTRIBUTING.md) to get started.
