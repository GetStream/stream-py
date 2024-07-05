# Official Python SDK for [Stream](https://getstream.io/)

[![build](https://github.com/GetStream/stream-py/actions/workflows/ci.yml/badge.svg)](https://github.com/GetStream/stream-py/actions) [![PyPI version](https://badge.fury.io/py/getstream.svg)](http://badge.fury.io/py/getstream) ![PyPI - Python Version](https://img.shields.io/pypi/pyversions/getstream.svg)

## Features

- Video call creation and management
- Chat session creation and management
- Token generation for user authentication
- Command-line interface (CLI) for easy interaction
- Docker support for containerized usage

## Installation

You can install the Stream Client Library using pip or pipx.

### Using pip

To install using pip, run the following command:

```sh
pip install getstream
```

### Using pipx

For a more isolated and manageable installation, especially for CLI tools, we recommend using pipx. Pipx installs the package in its own virtual environment, making it available globally while keeping it isolated from other Python packages.

First, install pipx if you haven't already:

```sh
python -m pip install --user pipx
python -m pipx ensurepath
```

Then, install the Stream Client Library using pipx:

```sh
pipx install getstream[cli]
pipx upgrade getstream
```

To uninstall the package, run:

```sh
pipx uninstall getstream
```

This will make the `getstream` CLI command available globally on your system.

> [!NOTE]
> Using pipx is particularly beneficial for the CLI functionality of the Stream SDK. It ensures that the CLI is always available without affecting your other Python projects or global Python environment.

After installation with pipx, you can run CLI commands directly:

```sh
getstream create-token --user-id your_user_id
```

For library usage in your Python projects, the standard pip installation is recommended.

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

## Command-Line Interface (CLI)

The Stream SDK includes a CLI for easy interaction with the API. You can use it to perform various operations such as creating tokens, managing video calls, and more.

To use the CLI, run:

```sh
python -m getstream.cli [command] [options]
```

For example, to create a token:

```sh
python -m getstream.cli create-token --user-id your_user_id
```

For more information on available commands, run:

```sh
python -m getstream.cli --help
```

## Docker Support

The Stream SDK can be run in a Docker container. This is useful for deployment and consistent development environments.

### Building the Docker Image

To build the Docker image, run:

```sh
make docker-build
```

### Running Commands in Docker

To run a CLI command using Docker:

```sh
make docker-run CMD='create-token --user-id your_user_id'
```

Make sure to set the `STREAM_API_KEY` and `STREAM_API_SECRET` environment variables when running Docker commands.

### Pushing the Docker Image

To push the Docker image to the GitHub Container Registry (usually done by CI):

```sh
make docker-push VERSION=1.0.0
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
make test
```

Before pushing changes make sure to have git hooks installed correctly, so that you get linting done locally `pre-commit install`

You can also run the code formatting yourself if needed:

```sh
make format
```

To run the linter:

```sh
make lint
```

To fix linter issues automatically:

```sh
make fix
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