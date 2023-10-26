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
First, build the image:

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

To run tests, run the following command:
```sh
# export secrets
export VIDEO_API_KEY=your_api_key
export VIDEO_API_SECRET=your_api_secret
poetry run pytest tests/
```

Before pushing changes make sure to run the linter:

```sh
poetry run black getstream/ tests/
```

### Code Generation

In order to generate the code, clone the `protocol` repo 
```sh
git clone github.com/GetStream/protocol
cd protocol
# checkout to the generator branch
git checkout PBE-832-openapi-generation-tool
# merge master into the generator branch to get the latest spec changes
git merge master
```

Then run the following command to generate the code
```sh
cd openapi-gen
go run . -i ../openapi/video-openapi.yaml -o ~/py-dev/stream/getstream  -c config.yaml # replicate with path to where you cloned the current repo
```

## License

This project is licensed under the [MIT License](LICENSE).

## Contributing

Contributions are welcome! Please read the [contributing guidelines](CONTRIBUTING.md) to get started.
