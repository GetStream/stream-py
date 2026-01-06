# Official Python SDK for [Stream](https://getstream.io/)

[![build](https://github.com/GetStream/stream-py/actions/workflows/ci.yml/badge.svg)](https://github.com/GetStream/stream-py/actions) [![PyPI version](https://badge.fury.io/py/getstream.svg)](http://badge.fury.io/py/getstream) ![PyPI - Python Version](https://img.shields.io/pypi/pyversions/getstream.svg)

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

If you want to build audio or video AI integrations, make sure to check [Vision-Agents](https://github.com/GetStream/Vision-Agents):

```sh
pip install getstream[webrtc]

# or using uv
uv add 'getstream[webrtc]'
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

### Getting Response Data

Many calls return a `StreamResponse` object, with the specific dataclass for the method call nested inside. You can access this via:

```python
response: StreamResponse[StartClosedCaptionsResponse] = call.start_closed_captions()
response.data  # Gives the StartClosedCaptionsResponse model
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

We use [uv](https://github.com/astral-sh/uv) to manage dependencies and run tests.

### 🚀 Quick Start

**Prerequisites:**
- Python 3.9+ (recommended: 3.12.2)
- [uv](https://github.com/astral-sh/uv) package manager

**Setup:**
```sh
# 1. Clone and enter the repository
git clone https://github.com/GetStream/stream-py.git
cd stream-py

# 2. Create virtual environment and install everything
uv venv --python 3.12.2
uv sync --all-extras --dev

# 3. Set up pre-commit hooks
pre-commit install

# 4. Create environment file for API credentials
cp .env.example .env
# Edit .env with your Stream API credentials
```

### 🧪 Testing

**Run all tests:**
```sh
uv run pytest                          # Everything
uv run pytest -v                       # Verbose output
uv run pytest -x                       # Stop on first failure
```

**Run specific test suites:**
```sh
# Main package tests
uv run pytest tests/
uv run pytest tests/test_video.py      # Specific test file
```

**Test with coverage:**
```sh
uv run pytest --cov=getstream --cov-report=html
```

**Test configuration:**
- Configuration: `pytest.ini`
- Fixtures: `tests/fixtures.py`
- Test assets: `tests/assets/` (keep files < 256KB)

**Testing best practices:**
- Write tests as simple Python functions with assert statements
- Use fixtures from `tests/fixtures.py` for common setup
- Place test assets in `tests/assets/` directory
- Avoid mocks unless specifically required
- Always run tests from the project root directory

**CI considerations:**
```python
import pytest

@pytest.mark.skip_in_ci
def test_something():
    # This test will be skipped in GitHub Actions
    ...
```

### 🎯 Common Tasks

**Install new dependency:**
```sh
# Main package
uv add "new-package>=1.0.0"

# Plugin-specific
cd getstream/plugins/stt/my-plugin/
uv add "plugin-specific-dep>=2.0.0"

# WebRTC-related (add to webrtc extra)
# Edit pyproject.toml [project.optional-dependencies] webrtc section
```

**Run linting and formatting:**
```sh
uv run ruff check getstream/ tests/        # Check for issues
uv run ruff format getstream/ tests/       # Format code
uv run pre-commit run --all-files          # Run all hooks
```

**Generate code:**

```sh
./generate_webrtc.sh                       # Regenerate WebRTC bindings
```

Note: regenerating code requires access to internal code available only to Stream developers

### 🐛 Troubleshooting

**Test failures:**
```sh
# Run with verbose output
uv run pytest -v -s

# Run specific test
uv run pytest tests/test_video.py::test_specific_function -v
```

## License

This project is licensed under the [MIT License](LICENSE).

## Contributing

Contributions are welcome! Please read the [contributing guidelines](CONTRIBUTING.md) to get started.
