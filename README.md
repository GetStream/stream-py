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

## Migrating from stream-chat?

If you are currently using [`stream-chat`](https://github.com/GetStream/stream-chat-python), we have a detailed migration guide with side-by-side code examples for common Chat use cases. See the [Migration Guide](docs/migration-from-stream-chat-python/README.md).

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

### Logging

The SDK emits structured log events (`client.initialized`, `http.request.sent`, `http.response.received`, `http.request.failed`) through the stdlib `logging` module. By default nothing is printed: pass a `logging.Logger` to see them.

```python
import logging

logging.basicConfig(level=logging.DEBUG)
client = Stream(api_key="key", api_secret="secret", logger=logging.getLogger("myapp.stream"))
```

Each event carries structured fields via the standard `extra={}` mechanism (for example `http.response.status_code`, `duration_ms`, `stream.endpoint_name`). Query and body values for known secret keys (`api_key`, `api_secret`, `token`, `password`) are always redacted. Request/response bodies are omitted by default; pass `log_bodies=True` to include them (still redacted, and this emits one WARNING at construction since bodies can contain other sensitive data).

### Retries

By default the client makes exactly one attempt per request and surfaces errors unchanged. Pass a `RetryConfig` to opt in to auto-retry:

```python
from getstream import Stream, RetryConfig

client = Stream(api_key=..., api_secret=..., retry=RetryConfig(enabled=True, max_attempts=3, max_backoff=30.0))
```

Only idempotent `GET`/`HEAD` requests are retried, and only on HTTP 429 (unless the backend marked it unrecoverable) or a transport-level failure (timeout, connection reset, DNS, TLS). A 429's `Retry-After` header is honored (clamped to `max_backoff`); otherwise the delay uses full jitter over an exponential backoff. A retried failure logs `http.request.failed` at DEBUG; a final, non-retried failure logs it at ERROR (or not at all for a final 429, since that's already covered by `http.response.received`).

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
- Python 3.10+ (recommended: 3.12.2)
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

## Releases

Releases are driven by [release-please](https://github.com/googleapis/release-please).

- Merge PRs to `main` with conventional-commit titles. The repo is squash-only with
  `squash_merge_commit_title: PR_TITLE`, so the PR title becomes the commit subject and
  decides the next version: `feat:` is a minor, `fix:` and `perf:` are a patch, `feat!:`
  or `<type>(scope)!:` is a major. Other types (`chore`, `ci`, `docs`, `test`,
  `refactor`) ship nothing. Both settings are load-bearing: release-please reads commit
  messages, never PR titles, and a merge commit's subject is not conventional.
- release-please keeps a Release PR open with the version bump in `pyproject.toml`,
  `uv.lock` and `CHANGELOG.md`. It is opened by `github-actions[bot]`, so approve it and
  run its held checks like any other PR.
- Merging the Release PR runs lint, type-check and the unit and integration matrix on
  that merge commit, which is the commit the tag will point at. Only if that is green
  does the workflow create the tag and the GitHub Release and publish to PyPI via
  Trusted Publishing (OIDC). The order matters: a tag and a GitHub Release cannot be
  withdrawn, a failed publish can be retried. If a later dispatch would tag a commit
  this run did not test, it fails rather than tagging it.

To retry a publish that failed after the release was tagged, use "Re-run failed jobs" on
that workflow run. Once GitHub has retired the run, dispatch `Release` from `main` with
`publish_tag` set to the tag (for example `v6.1.1`), which builds and publishes that tag
without touching release-please.

To force a specific version, type `Release-As: X.Y.Z` in the commit message box of the
squash dialog when merging a PR; the PR description is not copied there. To hotfix while
`main` carries unreleased work, branch `N.x` from the last tag, cherry-pick the fix, and
merge the Release PR that release-please opens against that branch.

`last-release-sha` in `release-please-config.json` is temporary. `v6.1.0` sits on a bump
commit the previous workflow created off-branch and never pushed, so release-please
cannot reach it by walking `main` and would otherwise treat the whole history as
unreleased. Delete the key once a release-please-created release exists on `main`; the
walk stops at that release commit before it reaches the pin.

## License

This project is licensed under the [MIT License](LICENSE).

## Contributing

Contributions are welcome! Please read the [contributing guidelines](CONTRIBUTING.md) to get started.
