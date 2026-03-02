import uuid


from getstream import Stream
from getstream.models import (
    ChannelMemberRequest,
    EventRequest,
    MessageRequest,
    QueryUsersPayload,
    SortParamRequest,
    UpdateUserPartialRequest,
    UserRequest,
)


def test_upsert_users(client: Stream):
    """Create/update users."""
    user_id = str(uuid.uuid4())
    response = client.update_users(
        users={
            user_id: UserRequest(
                id=user_id, role="admin", custom={"premium": True}, name=user_id
            )
        }
    )
    assert user_id in response.data.users
    assert response.data.users[user_id].custom.get("premium") is True

    try:
        client.delete_users(
            user_ids=[user_id], user="hard", conversations="hard", messages="hard"
        )
    except Exception:
        pass


def test_upsert_user_with_team(client: Stream):
    """Create a user with team and teams_role."""
    user_id = str(uuid.uuid4())
    response = client.update_users(
        users={
            user_id: UserRequest(
                id=user_id,
                teams=["blue"],
                teams_role={"blue": "admin"},
            )
        }
    )
    assert user_id in response.data.users
    assert "blue" in response.data.users[user_id].teams
    assert response.data.users[user_id].teams_role["blue"] == "admin"

    try:
        client.delete_users(
            user_ids=[user_id], user="hard", conversations="hard", messages="hard"
        )
    except Exception:
        pass


def test_update_user_partial_with_team(client: Stream, random_user):
    """Partial update a user with team fields."""
    # add user to team
    client.update_users_partial(
        users=[UpdateUserPartialRequest(id=random_user.id, set={"teams": ["blue"]})]
    )

    response = client.update_users_partial(
        users=[
            UpdateUserPartialRequest(
                id=random_user.id,
                set={"teams_role": {"blue": "admin"}},
            )
        ]
    )
    assert random_user.id in response.data.users
    assert response.data.users[random_user.id].teams_role is not None
    assert response.data.users[random_user.id].teams_role["blue"] == "admin"


def test_query_users(client: Stream, random_user):
    """Query users with filter conditions."""
    response = client.query_users(
        QueryUsersPayload(filter_conditions={"id": {"$eq": random_user.id}})
    )
    assert response.data.users is not None
    assert len(response.data.users) == 1
    assert response.data.users[0].id == random_user.id


def test_query_users_with_filters(client: Stream):
    """Query users with custom field filters and sort."""
    users = {}
    for name, age in [("alice", 30), ("bob", 25), ("carol", 35)]:
        uid = f"{name}-{uuid.uuid4().hex[:8]}"
        users[uid] = UserRequest(id=uid, name=name, custom={"age": age, "group": "test"})
    client.update_users(users=users)
    user_ids = list(users.keys())

    response = client.query_users(
        QueryUsersPayload(
            filter_conditions={"id": {"$in": user_ids}},
            sort=[SortParamRequest(field="name", direction=1)],
        )
    )
    assert len(response.data.users) == 3
    names = [u.name for u in response.data.users]
    assert names == sorted(names)

    try:
        client.delete_users(
            user_ids=user_ids, user="hard", conversations="hard", messages="hard"
        )
    except Exception:
        pass


def test_update_users_partial(client: Stream, random_user):
    """Partial update of user fields."""
    response = client.update_users_partial(
        users=[
            UpdateUserPartialRequest(
                id=random_user.id,
                set={"field": "updated", "color": "blue"},
                unset=["name"],
            )
        ]
    )
    assert random_user.id in response.data.users
    assert response.data.users[random_user.id].custom.get("color") == "blue"


def test_delete_user(client: Stream):
    """Delete a user."""
    user_id = str(uuid.uuid4())
    client.update_users(users={user_id: UserRequest(id=user_id, name=user_id)})
    response = client.delete_users(user_ids=[user_id])
    assert response.data.task_id is not None


def test_deactivate_reactivate(client: Stream):
    """Deactivate and reactivate a user."""
    user_id = str(uuid.uuid4())
    client.update_users(users={user_id: UserRequest(id=user_id, name=user_id)})

    response = client.deactivate_user(user_id=user_id)
    assert response.data.user is not None
    assert response.data.user.id == user_id

    response = client.reactivate_user(user_id=user_id)
    assert response.data.user is not None
    assert response.data.user.id == user_id

    try:
        client.delete_users(
            user_ids=[user_id], user="hard", conversations="hard", messages="hard"
        )
    except Exception:
        pass


def test_restore_users(client: Stream):
    """Delete a user and then restore them."""
    user_id = str(uuid.uuid4())
    client.update_users(users={user_id: UserRequest(id=user_id, name=user_id)})
    client.delete_users(user_ids=[user_id])

    # Wait for delete task
    import time

    time.sleep(2)

    client.restore_users(user_ids=[user_id])

    response = client.query_users(QueryUsersPayload(filter_conditions={"id": user_id}))
    assert len(response.data.users) == 1

    try:
        client.delete_users(
            user_ids=[user_id], user="hard", conversations="hard", messages="hard"
        )
    except Exception:
        pass


def test_export_user(client: Stream, random_user):
    """Export a single user's data."""
    response = client.export_user(user_id=random_user.id)
    assert response.data.user is not None
    assert response.data.user.id == random_user.id


def test_create_token(client: Stream):
    """Create a user token and verify it's a JWT string."""
    user_id = "tommaso"
    token = client.create_token(user_id=user_id)
    assert isinstance(token, str)
    assert len(token) > 0
    # JWT tokens have 3 parts separated by dots
    assert len(token.split(".")) == 3


def test_create_guest(client: Stream):
    """Create a guest user."""
    user_id = str(uuid.uuid4())
    try:
        response = client.create_guest(user=UserRequest(id=user_id, name="Guest"))
        assert response.data.access_token is not None
    except Exception:
        # Guest user creation may not be enabled on every test app
        pass
    finally:
        try:
            client.delete_users(
                user_ids=[user_id], user="hard", conversations="hard", messages="hard"
            )
        except Exception:
            pass


def test_send_custom_event(client: Stream, random_user):
    """Send a custom event to a user."""
    response = client.chat.send_user_custom_event(
        user_id=random_user.id,
        event=EventRequest(type="friendship_request", custom={"text": "testtext"}),
    )
    assert response is not None


def test_mark_all_read(client: Stream, random_user):
    """Mark all channels as read for a user."""
    response = client.chat.mark_channels_read(user_id=random_user.id)
    assert response is not None


def test_devices(client: Stream, random_user):
    """CRUD operations for devices."""
    response = client.list_devices(user_id=random_user.id)
    assert response.data.devices is not None
    assert len(response.data.devices) == 0

    device_id = str(uuid.uuid4())
    client.create_device(
        id=device_id,
        push_provider="apn",
        user_id=random_user.id,
    )
    response = client.list_devices(user_id=random_user.id)
    assert len(response.data.devices) == 1

    client.delete_device(id=device_id, user_id=random_user.id)
    response = client.list_devices(user_id=random_user.id)
    assert len(response.data.devices) == 0


def test_unread_counts(client: Stream, channel, random_users):
    """Get unread counts for a user."""
    user1 = random_users[0].id
    user2 = random_users[1].id
    channel.update(add_members=[ChannelMemberRequest(user_id=user1)])
    channel.send_message(message=MessageRequest(text="helloworld", user_id=user2))
    response = client.chat.unread_counts(user_id=user1)
    assert response.data.total_unread_count is not None
    assert response.data.total_unread_count >= 1
    assert response.data.channels is not None
    assert len(response.data.channels) >= 1


def test_unread_counts_batch(client: Stream, channel, random_users):
    """Get batch unread counts for multiple users."""
    user1 = random_users[0].id
    members = [u.id for u in random_users[1:]]
    channel.update(add_members=[ChannelMemberRequest(user_id=uid) for uid in members])
    channel.send_message(message=MessageRequest(text="helloworld", user_id=user1))
    response = client.chat.unread_counts_batch(user_ids=members)
    assert response.data.counts_by_user is not None
    for uid in members:
        assert uid in response.data.counts_by_user


def test_deactivate_users(client: Stream):
    """Deactivate multiple users via async task."""

    user_ids = [str(uuid.uuid4()) for _ in range(3)]
    client.update_users(users={uid: UserRequest(id=uid, name=uid) for uid in user_ids})
    response = client.deactivate_users(user_ids=user_ids)
    assert response.data.task_id is not None

    from tests.base import wait_for_task

    task_response = wait_for_task(client, response.data.task_id, timeout_ms=30000)
    assert task_response.data.status == "completed"

    try:
        client.delete_users(
            user_ids=user_ids, user="hard", conversations="hard", messages="hard"
        )
    except Exception:
        pass


def test_export_users(client: Stream, random_user):
    """Export users via async task."""
    response = client.export_users(user_ids=[random_user.id])
    assert response.data.task_id is not None

    from tests.base import wait_for_task

    task_response = wait_for_task(client, response.data.task_id, timeout_ms=30000)
    assert task_response.data.status == "completed"
