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

If you want to use WebRTC, audio, or video functionality (like real-time call joining, audio processing, STT/TTS plugins), install with the webrtc extra:

```sh
pip install getstream[webrtc]

# or using uv
uv add 'getstream[webrtc]'
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

We use [uv](https://github.com/astral-sh/uv) to manage dependencies and run tests. This project uses a **UV workspace** configuration that makes development across the main package, plugins, and examples seamless.

### 🏗️ Repository Structure

```
stream-py/
├── pyproject.toml              # Root workspace configuration
├── uv.lock                     # Unified dependency lock file
├── getstream/                  # Main SDK package
│   └── plugins/                # Plugin packages
│       ├── stt/deepgram/       # Speech-to-text plugins
│       ├── tts/elevenlabs/     # Text-to-speech plugins
│       └── vad/silero/         # Voice activity detection plugins
├── examples/                   # Example projects
│   └── stt_deepgram_transcription/
├── tests/                      # Main package tests
└── ai/instructions/            # Development guides
```

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

### 🔧 UV Workspace Benefits

The workspace configuration provides:
- ✅ **Automatic editable installs**: All packages linked automatically
- ✅ **Live updates**: Changes propagate instantly across packages
- ✅ **Unified dependencies**: Single lock file for consistent versions
- ✅ **Simple testing**: Run tests across the entire codebase
- ✅ **Easy plugin development**: No manual dependency management

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

# Plugin tests
uv run pytest getstream/plugins/stt/deepgram/tests/
uv run pytest getstream/plugins/*/tests/           # All plugins

# Example tests
uv run pytest examples/stt_deepgram_transcription/tests/
uv run pytest examples/*/tests/                    # All examples
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

### 🔨 Development Workflows

#### Working on the Main Package

```sh
# Make changes to getstream/
# Run tests to verify
uv run pytest tests/

# Changes are immediately available to plugins and examples
```

#### Working on Plugins

```sh
# Make changes to getstream/plugins/stt/your-plugin/
# Run plugin tests
uv run pytest getstream/plugins/stt/your-plugin/tests/

# Test integration with examples
cd examples/your-example/
uv run python main.py
```

#### Creating a New Plugin

```sh
# 1. Create plugin directory
mkdir -p getstream/plugins/stt/my-plugin

# 2. Add pyproject.toml with workspace source
cat > getstream/plugins/stt/my-plugin/pyproject.toml << EOF
[project]
name = "getstream-plugins-stt-my-plugin"
dependencies = ["getstream[webrtc]"]

[tool.uv.sources]
getstream = { workspace = true }
EOF

# 3. Add to workspace members in root pyproject.toml
# Edit: [tool.uv.workspace] members = [..., "getstream/plugins/stt/my-plugin"]

# 4. Sync workspace
uv sync --all-extras --dev
```

#### Working on Examples

```sh
# Examples automatically use local versions
cd examples/stt_deepgram_transcription/
uv run python main.py

# Add new example
mkdir examples/my-example
# Create pyproject.toml with workspace sources
# Add to workspace members
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

**Generate WebRTC code:**
```sh
./generate_webrtc.sh                       # Regenerate WebRTC bindings
```

**Generate API code:**
```sh
./generate.sh                              # Regenerate API endpoints
```

### 🐛 Troubleshooting

**Workspace sync issues:**
```sh
# Clean and reinstall
uv sync --reinstall --all-extras --dev
```

**Import errors:**
```sh
# Ensure you're running from project root
cd /path/to/stream-py
uv run python -c "import getstream; print('✅ Import successful')"
```

**Test failures:**
```sh
# Run with verbose output
uv run pytest -v -s

# Run specific test
uv run pytest tests/test_video.py::test_specific_function -v
```

**Plugin not found:**
```sh
# Check workspace members in pyproject.toml
# Ensure plugin has [tool.uv.sources] getstream = { workspace = true }
# Re-sync workspace
uv sync --all-extras --dev
```

### 📚 Additional Resources

- **Plugin Development**: See `ai/instructions/projects/ai-plugin.md`
- **Testing Guidelines**: See `ai/instructions/ai-basics.md`
- **WebRTC Setup**: See `ai/instructions/ai-webrtc.md`
- **Examples**: Browse `examples/` directory for usage patterns

## License

This project is licensed under the [MIT License](LICENSE).

## Contributing

Contributions are welcome! Please read the [contributing guidelines](CONTRIBUTING.md) to get started.
