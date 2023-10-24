import os
import uuid

import pytest
from getstream.models.user_request import UserRequest
from getstream import Stream


VIDEO_API_KEY = os.environ.get("VIDEO_API_KEY")
BASE_URL = "https://video.stream-io-api.com/video"
VIDEO_API_SECRET = os.environ.get("VIDEO_API_SECRET")
TIMEOUT = 6


@pytest.fixture(scope="module")
def client():
    return Stream(
        api_key=VIDEO_API_KEY,
        api_secret=VIDEO_API_SECRET,
        timeout=TIMEOUT,
        video_base_url=BASE_URL,
    )


def test_update_users(client: Stream):
    users = {}
    user_id = str(uuid.uuid4())
    users[user_id] = UserRequest(
        id=user_id, role="admin", custom={"premium": True}, name=user_id
    )

    client.users.update_users(users=users)


def test_query_users(client: Stream):
    response = client.users.query_users(limit=10)
    assert response.users is not None


def test_delete_user(client: Stream):
    user_id = str(uuid.uuid4())
    # create user to ban
    users = {}
    users[user_id] = UserRequest(
        id=user_id, role="admin", custom={"premium": True}, name=user_id
    )
    client.users.update_users(users=users)
    client.users.delete_user(user_id=user_id)
    response = client.users.query_users(limit=10)
    # check that user id is not in the response
    user_ids = [user.id for user in response.users]
    assert user_id not in user_ids
