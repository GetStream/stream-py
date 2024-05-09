import uuid

from getstream import Stream
from getstream.models import (
    CallRequest,
    CallSettingsRequest,
    ScreensharingSettingsRequest,
    OwnCapability,
)
from getstream.video.call import Call


def test_setup_client():
    from getstream import Stream

    client = Stream(api_key="your_api_key", api_secret="your_api_secret")
    assert isinstance(client, Stream)
    assert client.api_key == "your_api_key"
    assert client.api_secret == "your_api_secret"
    assert client.timeout == 6.0


def test_create_user(client: Stream):
    from getstream.models import UserRequest

    client.upsert_users(
        UserRequest(
            id="tommaso-id", name="tommaso", role="admin", custom={"country": "NL"}
        ),
        UserRequest(
            id="thierry-id", name="thierry", role="admin", custom={"country": "US"}
        ),
    )

    token = client.create_token("tommaso-id")
    assert token


def test_create_call_with_members(client: Stream):
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


def test_ban_unban_user(client: Stream, get_user):
    bad_user = get_user()
    moderator = get_user()
    client.ban(
        target_user_id=bad_user.id,
        banned_by_id=moderator.id,
        reason="Banned user and all users sharing the same IP for half hour",
        ip_ban=True,
        timeout=30,
    )

    client.unban(target_user_id=bad_user.id)


def test_block_unblock_user_from_calls(client: Stream, call: Call, get_user):
    bad_user = get_user()
    call.get_or_create(
        data=CallRequest(
            created_by_id="tommaso-id",
        )
    )
    call.block_user(bad_user.id)
    response = call.get()
    assert len(response.data.call.blocked_user_ids) == 1

    call.unblock_user(bad_user.id)
    response = call.get()
    assert len(response.data.call.blocked_user_ids) == 0


def test_update_settings(call: Call):
    user_id = str(uuid.uuid4())

    call.get_or_create(
        data=CallRequest(
            created_by_id=user_id,
        )
    )

    call.update(
        settings_override=CallSettingsRequest(
            screensharing=ScreensharingSettingsRequest(
                enabled=True, access_request_enabled=True
            ),
        ),
    )


def test_mute_all(call: Call):
    user_id = str(uuid.uuid4())
    call.get_or_create(
        data=CallRequest(
            created_by_id=user_id,
        )
    )

    call.mute_users(
        muted_by_id=user_id,
        mute_all_users=True,
        audio=True,
    )


def test_mute_some_users(call: Call, get_user):
    alice = get_user()
    bob = get_user()

    user_id = str(uuid.uuid4())
    call.get_or_create(
        data=CallRequest(
            created_by_id=user_id,
        )
    )

    call.mute_users(
        muted_by_id=user_id,
        user_ids=[alice.id, bob.id],
        audio=True,
        video=True,
        screenshare=True,
        screenshare_audio=True,
    )


def test_update_user_permissions(call: Call, get_user):
    user_id = str(uuid.uuid4())
    call.get_or_create(
        data=CallRequest(
            created_by_id=user_id,
        )
    )

    alice = get_user()
    call.update_user_permissions(
        user_id=alice.id,
        revoke_permissions=[OwnCapability.SEND_AUDIO],
    )

    call.update_user_permissions(
        user_id=alice.id,
        grant_permissions=[OwnCapability.SEND_AUDIO],
    )


def test_deactivate_user(client: Stream, get_user):
    alice = get_user()
    bob = get_user()

    # deactivate one user
    client.deactivate_user(user_id=alice.id)

    # reactivates the user
    client.reactivate_user(user_id=alice.id)

    # deactivates users in bulk, this is an async operation
    response = client.deactivate_users(user_ids=[alice.id, bob.id])
    task_id = response.data.task_id

    # this is just an example, in reality it can take a few seconds for a task to be processed
    task_status = client.get_task(task_id)

    if task_status.data.status == "completed":
        print(task_status.data.result)
