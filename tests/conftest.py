import functools
import uuid
import pytest
import os
from dotenv import load_dotenv
from tests.fixtures import (
    client,
    call,
    get_user,
    shared_call,
    test_feed,
    get_feed,
    async_client,
)

from getstream import Stream
from getstream.models import UserRequest, ChannelInput

__all__ = [
    "client",
    "call",
    "get_user",
    "shared_call",
    "test_feed",
    "get_feed",
    "async_client",
    "channel",
    "random_user",
    "random_users",
    "server_user",
]


@pytest.fixture
def random_user(client: Stream):
    user_id = str(uuid.uuid4())
    response = client.update_users(
        users={user_id: UserRequest(id=user_id, name=user_id)}
    )
    assert user_id in response.data.users
    yield response.data.users[user_id]
    try:
        client.delete_users(
            user_ids=[user_id], user="hard", conversations="hard", messages="hard"
        )
    except Exception:
        pass


@pytest.fixture
def random_users(client: Stream):
    users = []
    user_ids = []
    for _ in range(3):
        uid = str(uuid.uuid4())
        user_ids.append(uid)
        users.append(UserRequest(id=uid, name=uid))
    response = client.update_users(users={u.id: u for u in users})
    yield [response.data.users[uid] for uid in user_ids]
    try:
        client.delete_users(
            user_ids=user_ids, user="hard", conversations="hard", messages="hard"
        )
    except Exception:
        pass


@pytest.fixture
def server_user(client: Stream):
    user_id = str(uuid.uuid4())
    response = client.update_users(
        users={user_id: UserRequest(id=user_id, name="server-admin")}
    )
    assert user_id in response.data.users
    yield response.data.users[user_id]
    try:
        client.delete_users(
            user_ids=[user_id], user="hard", conversations="hard", messages="hard"
        )
    except Exception:
        pass


@pytest.fixture
def channel(client: Stream, random_user):
    channel_id = str(uuid.uuid4())
    ch = client.chat.channel("messaging", channel_id)
    ch.get_or_create(
        data=ChannelInput(
            created_by_id=random_user.id,
            custom={"test": True, "language": "python"},
        )
    )
    yield ch
    try:
        client.chat.delete_channels(cids=[f"messaging:{channel_id}"], hard_delete=True)
    except Exception:
        pass


@pytest.fixture(scope="session", autouse=True)
def load_env():
    load_dotenv()


def pytest_configure(config):
    """Register custom markers."""
    config.addinivalue_line(
        "markers", "skip_in_ci: mark test to skip when running in CI"
    )


def is_running_in_github_actions():
    """Check if the tests are running in GitHub Actions CI."""
    return os.environ.get("GITHUB_ACTIONS") == "true"


def pytest_runtest_setup(item):
    """Skip tests marked with skip_in_ci when running in GitHub Actions."""
    if is_running_in_github_actions():
        skip_in_ci_marker = item.get_closest_marker("skip_in_ci")
        if skip_in_ci_marker is not None:
            pytest.skip("Test skipped in CI environment")


def skip_on_rate_limit(func):
    """Skip test if it fails due to rate limiting."""
    from getstream.video.rtc.coordinator.errors import StreamWSConnectionError

    @functools.wraps(func)
    async def wrapper(*args, **kwargs):
        try:
            return await func(*args, **kwargs)
        except StreamWSConnectionError as e:
            if "did not receive a valid http response" in str(e).lower():
                pytest.skip(f"Skipped due to rate limiting: {e}")
            raise

    return wrapper
