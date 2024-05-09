# Official Python SDK for [Stream](https://getstream.io/)

[![build](https://github.com/GetStream/stream-py/actions/workflows/ci.yml/badge.svg)](https://github.com/GetStream/stream-py/actions) [![PyPI version](https://badge.fury.io/py/getstream.svg)](http://badge.fury.io/py/getstream) ![PyPI - Python Version](https://img.shields.io/pypi/pyversions/getstream.svg)

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
from getstream.models import UserRequest

# sync two users using the update_users method, both users will get insert or updated
client.upsert_users(
    UserRequest(
        id="tommaso-id", name="tommaso", role="admin", custom={"country": "NL"}
    ),
    UserRequest(
        id="thierry-id", name="thierry", role="admin", custom={"country": "US"}
    ),
)

# Create a JWT token for the user to connect client-side (e.g. browser/mobile app)
token = client.create_token("tommaso-id")
```

### Video API - Calls

To create a video call, use the `client.video.call` method:

```python
import uuid
from getstream.models import (
    CallRequest,
    MemberRequest,
)

call = client.video.call("default", uuid.uuid4())
call.get_or_create(
    data=CallRequest(
        created_by_id="tommaso-id",
        members=[
            MemberRequest(user_id="thierry-id"),
            MemberRequest(user_id="tommaso-id"),
        ],
    ),
)
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

# TODO: implement and call chat-related methods with chat_instance
```

## Development

We use poetry to manage dependencies and run tests. It's a package manager for Python that allows you to declare the libraries your project depends on and manage them.
To install the development dependencies, run the following command:

```sh
poetry install
pre-commit install
```

To activate the virtual environment, run the following command:

```sh
poetry shell
```

To run tests, create a `.env` using the `.env.example` and adjust it to have valid API credentials
```sh
poetry run pytest tests/ getstream/
```

Before pushing changes make sure to have git hooks installed correctly, so that you get linting done locally `pre-commit install`

You can also run the code formatting yourself if needed:

```sh
poetry run ruff format getstream/ tests/
```

### Writing new tests

pytest is used to run tests and to inject fixtures, simple tests can be written as simple python functions making assert calls. Make sure to have a look at the available test fixtures under `tests/fixtures.py`

### Generate code from spec

To regenerate the Python source from OpenAPI, just run the `./generate.sh` script from this repo.

> [!NOTE]
> Code generation currently relies on tooling that is not publicly available, only Stream devs can regenerate SDK source code from the OpenAPI spec.

## License

This project is licensed under the [MIT License](LICENSE).

## Contributing

Contributions are welcome! Please read the [contributing guidelines](CONTRIBUTING.md) to get started.
