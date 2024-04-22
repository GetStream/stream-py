import os
import uuid

import pytest
from getstream.models import UpdateUserPartialRequest, UpdateUsersRequest, UpdateUsersPartialRequest, QueryUsersPayload, \
    DeleteUsersRequest, ReactivateUsersRequest
from getstream.models import UserRequest
from getstream import Stream

def test_upsert_users(client: Stream):
    users = {}
    user_id = str(uuid.uuid4())
    users[user_id] = UserRequest(
        id=user_id, role="admin", custom={"premium": True}, name=user_id
    )

    client.update_users(update_users_request=UpdateUsersRequest(users=users))


def test_query_users(client: Stream):
    response = client.query_users(QueryUsersPayload(filter_conditions={}))
    assert response.data.users is not None


def test_update_users_partial(client: Stream):
    user_id = str(uuid.uuid4())
    users = {user_id: UserRequest(
        id=user_id, role="admin", custom={"premium": True}, name=user_id
    )}
    client.update_users(update_users_request=UpdateUsersRequest(users=users))
    response = client.update_users_partial(
        update_users_partial_request=UpdateUsersPartialRequest([
            UpdateUserPartialRequest(
                id=user_id,
                set={"role": "admin", "color": "blue"},
                unset=["name"],
            )
        ])
    )
    assert user_id in response.data.users
    assert response.data.users[user_id].name is None
    assert response.data.users[user_id].role == "admin"
    assert response.data.users[user_id].custom["color"] == "blue"


def test_deactivate_and_reactivate_users(client: Stream):
    user_id = str(uuid.uuid4())
    users = {
        user_id: UserRequest(id=user_id, role="admin", custom={"premium": True}, name=user_id)
    }

    client.update_users(UpdateUsersRequest(users))
    response = client.deactivate_user(user_id)
    assert response.data.user.id == user_id

    response = client.reactivate_users(ReactivateUsersRequest(user_ids=[user_id]))
    assert response.data.task_id is not None


def test_delete_user(client: Stream):
    user_id = str(uuid.uuid4())
    users = {
        user_id: UserRequest(id=user_id, role="admin", custom={"premium": True}, name=user_id)
    }
    client.update_users(UpdateUsersRequest(users=users))
    client.delete_users(DeleteUsersRequest(user_ids=[user_id]))
    response = client.query_users(QueryUsersPayload(filter_conditions={}, limit=10))
    # check that user id is not in the response
    user_ids = [user.id for user in response.data.users]
    assert user_id not in user_ids
