# Official Python SDK for [Stream](https://getstream.io/)

<div align="center">
  <picture>
    <source media="(prefers-color-scheme: dark)" srcset="https://github.com/user-attachments/assets/19dd203e-c84a-4015-9c90-1a54212fc2e2">
    <source media="(prefers-color-scheme: light)" srcset="https://github.com/user-attachments/assets/fb6b6686-ce5d-4c8f-87b7-9bb495b6ce66">
    <img src="https://github.com/user-attachments/assets/19dd203e-c84a-4015-9c90-1a54212fc2e2" width="360" alt="Stream logo">
  </picture>
  
[![build](https://github.com/GetStream/stream-py/actions/workflows/ci.yml/badge.svg)](https://github.com/GetStream/stream-py/actions) [![PyPI version](https://badge.fury.io/py/getstream.svg)](http://badge.fury.io/py/getstream) ![PyPI - Python Version](https://img.shields.io/pypi/pyversions/getstream.svg)
</div>



Check out our:

- ⭐ [Chat API](https://getstream.io/chat/)
- 📱 [Video API](https://getstream.io/video/)
- 🔔 [Activity Feeds](https://getstream.io/activity-feeds/)

## Features

- Video call creation and management
- Chat session creation and management
- Token generation for user authentication

## Installation

To install the Stream Client Library, run the following command:

```sh
pip install getstream

# or if like us, you fell in love with uv
uv add getstream
```

If you want to use the openai realtime integration, you need to install the package with the additional dependencies:

```sh
pip install getstream[openai-realtime]

# or using uv
uv add 'getstream[openai-realtime]'
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

We use [uv](https://github.com/astral-sh/uv) to manage dependencies and run tests. It's a package manager for Python that allows you to declare the libraries your project depends on and manage them.
To install the development dependencies, run the following command:

```sh
uv venv --python 3.12.2
uv sync --all-extras --dev
pre-commit install
```

To run tests, create a `.env` using the `.env.example` and adjust it to have valid API credentials
```sh
uv run pytest tests/ getstream/
```

Before pushing changes make sure to have git hooks installed correctly, so that you get linting done locally `pre-commit install`

You can also run the code formatting yourself if needed:

```sh
uv run ruff format getstream/ tests/
```

### Writing new tests

pytest is used to run tests and to inject fixtures, simple tests can be written as simple python functions making assert calls. Make sure to have a look at the available test fixtures under `tests/fixtures.py`

#### Skipping Tests in CI

Some tests may not be suitable for running in a CI environment (GitHub Actions). To skip a test in CI, use the `@pytest.mark.skip_in_ci` decorator:

```python
import pytest

@pytest.mark.skip_in_ci
def test_something():
    # This test will be skipped when running in GitHub Actions
    ...
```

The test will run normally in local development environments but will be automatically skipped when running in GitHub Actions.

### Generate code from spec

To regenerate the Python source from OpenAPI, just run the `./generate.sh` script from this repo.

> [!NOTE]
> Code generation currently relies on tooling that is not publicly available, only Stream devs can regenerate SDK source code from the OpenAPI spec.

## 🔍 Why Choose Stream?

[Stream](https://getstream.io) powers chat and activity feeds for over 1 billion end users. Our robust, scalable platform helps you build:

- **In-app Messaging** - Group chats, direct messaging, channels
- **Team Collaboration** - Slack-like workspaces and threaded conversations
- **Live Streaming** - Interactive live streams with chat
- **Virtual Events** - Engaging event platforms with rich chat features
- **Gaming Communities** - Community building with real-time chat
- **Support Channels** - Customer support with integrated chat

### ✨ Try Stream for Free

Ready to add chat to your application? [Sign up for a free Stream account](https://getstream.io/chat/trial/) and start building today!

* Free tier for smaller applications and testing
* Comprehensive documentation and tutorials
* Enterprise-grade security and compliance
* Dedicated support for paid plans

**[🔗 Check out our interactive demos →](https://getstream.io/chat/demos/)**

## 👩‍💻 We're Hiring!

We've [raised $38 million in Series B funding](https://techcrunch.com/2021/03/04/stream-raises-38m-as-its-chat-and-activity-feed-apis-power-communications-for-1b-users/) and are actively expanding our team of talented engineers.

Join us in building communication APIs used by over a billion end-users. You'll have the opportunity to make a significant impact on our products alongside some of the best engineers from around the world.

[**View Open Positions →**](https://getstream.io/team/#jobs)

## License

This project is licensed under the [MIT License](LICENSE).

## Contributing

Contributions are welcome! Please read the [contributing guidelines](CONTRIBUTING.md) to get started.
