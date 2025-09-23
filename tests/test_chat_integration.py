import pytest
import uuid

from getstream.models import (
    UpdateUserPartialRequest,
    QueryUsersPayload,
    MessageRequest,
    ChannelInput,
)
from getstream.models import UserRequest
from getstream import Stream, AsyncStream
import warnings


def test_upsert_users(client: Stream):
    users = {}
    user_id = str(uuid.uuid4())
    users[user_id] = UserRequest(
        id=user_id, role="admin", custom={"premium": True}, name=user_id
    )

    client.update_users(users=users)


def test_query_users(client: Stream):
    response = client.query_users(QueryUsersPayload(filter_conditions={}))
    assert response.data.users is not None


def test_update_users_partial(client: Stream):
    user_id = str(uuid.uuid4())
    users = {
        user_id: UserRequest(
            id=user_id, role="admin", custom={"premium": True}, name=user_id
        )
    }
    client.update_users(users=users)
    response = client.update_users_partial(
        users=[
            UpdateUserPartialRequest(
                id=user_id,
                set={"role": "admin", "color": "blue"},
                unset=["name"],
            )
        ]
    )
    assert user_id in response.data.users
    assert not response.data.users[user_id].name
    assert response.data.users[user_id].role == "admin"
    assert response.data.users[user_id].custom["color"] == "blue"


def test_deactivate_and_reactivate_users(client: Stream):
    user_id = str(uuid.uuid4())
    users = {
        user_id: UserRequest(
            id=user_id, role="admin", custom={"premium": True}, name=user_id
        )
    }

    client.update_users(users=users)
    response = client.deactivate_user(user_id)
    assert response.data.user.id == user_id

    response = client.reactivate_users(user_ids=[user_id])
    assert response.data.task_id is not None


def test_delete_user(client: Stream):
    user_id = str(uuid.uuid4())
    users = {
        user_id: UserRequest(
            id=user_id, role="admin", custom={"premium": True}, name=user_id
        )
    }
    client.update_users(users=users)
    client.delete_users(user_ids=[user_id])
    response = client.query_users(QueryUsersPayload(filter_conditions={}, limit=10))
    # check that user id is not in the response
    user_ids = [user.id for user in response.data.users]
    assert user_id not in user_ids


@pytest.mark.asyncio
async def test_send_message(async_client: AsyncStream):
    channel = async_client.chat.channel("messaging", str(uuid.uuid4()))
    await channel.get_or_create(
        data=ChannelInput(created_by_id="test-user-id", custom={"color": "black"})
    )
    await channel.send_message(
        message=MessageRequest(text="Hello, world!", user_id="test-user-id")
    )


def test_from_env():
    # Suppress the deprecation warning for this explicit compatibility check
    with warnings.catch_warnings():
        warnings.simplefilter("ignore", category=DeprecationWarning)
        Stream.from_env()
