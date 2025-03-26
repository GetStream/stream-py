## Project setup

1. This project uses `uv`,  `pyproject.toml` and venv to manage dependencies
2. Never use pip directly, use `uv add` to add dependencies and `uv sync --all-extras --dev` to install the dependency
3. Do not change codegenerate python code, `./generate.sh` is the script responsible of rebuilding all API endpoints and API models

## Python testing

1. pytest is used for testing
2. use `uv run pytest` to run tests
3. pytest preferences are stored in pytest.ini
4. fixtures are used to inject objects in tests
5. test using the Stream API client can use the fixture
6. .env is used to load credentials, the client fixture will load credentials from there
7. keep tests well organized and use test classes for similar tests
8. tests that rely on file assets should always rely on files inside the `tests/assets/` folder, new files should be added there and existing ones used if possible. Do not use files larger than 256 kilobytes.
9- do not use mocks or mock things in general unless you are asked to do that directly

## Project layout

1. the `getstream` folder is where all code lives
2. all tests live inside `tests`
3. each product (chat, video, feeds, moderation, ...) has its own sub-folder

## Initializing the SDK

In most cases you can get an already initialized API client from the test fixture, for example apps or other cases you can initialize the client like this:

```python
from getstream import Stream

client = Stream(api_key="your_api_key", api_secret="your_api_secret")
```

this gives you the top-level client which exposes use endpoints and other endpoints that are common to all products

### Video API endpoints

Product specific endpoints are nested inside the top-level client:

```python
call = client.video.call("default", uuid.uuid4())
```

### Call endpoints

Call is the main API resource on video and it exposes endpoints to interact with one call directly

```python
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

### Request and response models

All API endpoints deal with request and response types, everything is typed. To keep things simple all request and response types are defined inside the `getstream.models` module.

IMPORTANT: when writing code that works with client methods, make sure to look at its definition to understand the expected request and response types, do not try to guess names.

### API exceptions

When calling a client method that does an API call, an exception will be thrown if the response has a 4xx or 5xx status code. The `getstream.base.StreamAPIException` exception is thrown and it contains the response object under the `response` field.
