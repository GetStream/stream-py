import uuid
from typing import Dict

import pytest

from getstream import Stream
from getstream.models import UserRequest, FullUserResponse


def _client():
    return Stream.from_env()


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
