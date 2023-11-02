import os
import uuid

import pytest
from getstream.chat.models.update_user_partial_request import UpdateUserPartialRequest
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


def test_upsert_users(client: Stream):
    users = {}
    user_id = str(uuid.uuid4())
    users[user_id] = UserRequest(
        id=user_id, role="admin", custom={"premium": True}, name=user_id
    )

    client.upsert_users(users=users)


def test_query_users(client: Stream):
    response = client.query_users(limit=10)
    assert response.users is not None


def test_update_users_partial(client: Stream):
    user_id = str(uuid.uuid4())
    users = {}
    users[user_id] = UserRequest(
        id=user_id, role="admin", custom={"premium": True}, name=user_id
    )
    client.upsert_users(users=users)
    response = client.update_users_partial(
        users=[
            UpdateUserPartialRequest(
                id=user_id,
                set={"role": "admin", "color": "blue"},
                unset=["name"],
            )
        ]
    )
    response.users[user_id]


#     assert user_response["name"] is None
#     assert user_response["role"] == "admin"
#     assert user_response["custom"]["color"] == "blue"


def test_deactive_and_reactivate_users(client: Stream):
    user_id = str(uuid.uuid4())

    users = {}
    users[user_id] = UserRequest(
        id=user_id, role="admin", custom={"premium": True}, name=user_id
    )
    client.upsert_users(users=users)
    deactivateResponse = client.deactivate_user(user_id=user_id)
    assert deactivateResponse.user.id == user_id
    reactivateResponse = client.reactivate_users(user_ids=[user_id])
    assert reactivateResponse.task_id is not None


def test_delete_user(client: Stream):
    user_id = str(uuid.uuid4())
    users = {}
    users[user_id] = UserRequest(
        id=user_id, role="admin", custom={"premium": True}, name=user_id
    )
    client.upsert_users(users=users)
    client.delete_user(user_id=user_id)
    response = client.query_users(limit=10)
    # check that user id is not in the response
    user_ids = [user.id for user in response.users]
    assert user_id not in user_ids
