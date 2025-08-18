import os
import uuid
from typing import Dict

import pytest

from getstream import Stream
from getstream.models import UserRequest, FullUserResponse
from getstream.feeds.feeds import Feed


def _client():
    return Stream(
        api_key=os.environ.get("STREAM_API_KEY"),
        api_secret=os.environ.get("STREAM_API_SECRET"),
        base_url=os.environ.get("STREAM_BASE_URL"),
    )


@pytest.fixture
def client():
    return _client()


@pytest.fixture
def call(client: Stream):
    return client.video.call("default", str(uuid.uuid4()))


@pytest.fixture(scope="class")
def shared_call(request):
    """
    Use this fixture to decorate test classes subclassing base.VideoTestClass

    """
    request.cls.client = _client()
    request.cls.call = request.cls.client.video.call("default", str(uuid.uuid4()))


@pytest.fixture
def get_user(client: Stream):
    def inner(
        name: str = None, image: str = None, custom: Dict[str, object] = None
    ) -> FullUserResponse:
        id = str(uuid.uuid4())
        return client.upsert_users(
            UserRequest(
                id=id,
                name=name,
                image=image,
                custom=custom,
            ),
        ).data.users[id]

    return inner


@pytest.fixture
def test_feed(client: Stream):
    """Create a test feed for integration testing"""
    user_id = f"test-user-{uuid.uuid4()}"
    return client.feeds.feed("user", user_id)


@pytest.fixture
def get_feed(client: Stream):
    """Factory fixture for creating feeds"""
    def inner(feed_type: str = "user", feed_id: str = None, custom_data: Dict = None) -> Feed:
        if feed_id is None:
            feed_id = f"test-{feed_type}-{uuid.uuid4()}"
        return client.feeds.feed(feed_type, feed_id, custom_data)
    
    return inner
