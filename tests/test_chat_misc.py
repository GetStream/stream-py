import time
import uuid

import pytest

from getstream import Stream
from getstream.base import StreamAPIException
from getstream.chat.channel import Channel
from getstream.models import (
    EventHook,
    MessageRequest,
    SortParamRequest,
)


def test_get_app_settings(client: Stream):
    """Get application settings."""
    response = client.get_app()
    assert response.data.app is not None


def test_update_app_settings(client: Stream):
    """Update app settings and verify."""
    response = client.update_app()
    assert response is not None


def test_update_app_settings_event_hooks(client: Stream):
    """Update app settings with event hooks, then clear them."""
    response = client.update_app(
        event_hooks=[
            EventHook(
                hook_type="webhook",
                webhook_url="https://example.com/webhook",
                event_types=["message.new", "message.updated"],
            ),
        ]
    )
    assert response is not None

    settings = client.get_app()
    assert settings.data.app is not None

    # clear hooks
    client.update_app(event_hooks=[])


def test_blocklist_crud(client: Stream):
    """Full CRUD cycle for blocklists."""
    name = f"test-blocklist-{uuid.uuid4().hex[:8]}"

    # create
    client.create_block_list(name=name, words=["fudge", "heck"], type="word")

    # get
    response = client.get_block_list(name=name)
    assert response.data.blocklist is not None
    assert response.data.blocklist.name == name
    assert "fudge" in response.data.blocklist.words

    # list
    response = client.list_block_lists()
    assert response.data.blocklists is not None
    names = [bl.name for bl in response.data.blocklists]
    assert name in names

    # update
    client.update_block_list(name=name, words=["dang"])
    response = client.get_block_list(name=name)
    assert response.data.blocklist.words == ["dang"]

    # delete
    client.delete_block_list(name=name)


def test_list_channel_types(client: Stream):
    """List all channel types."""
    response = client.chat.list_channel_types()
    assert response.data.channel_types is not None
    assert len(response.data.channel_types) > 0


def test_get_channel_type(client: Stream):
    """Get a specific channel type."""
    response = client.chat.get_channel_type(name="team")
    assert response.data.permissions is not None


def test_update_channel_type(client: Stream):
    """Update a channel type's configuration."""
    # Get current config to know the required fields
    current = client.chat.get_channel_type(name="team")
    response = client.chat.update_channel_type(
        name="team",
        automod=current.data.automod,
        automod_behavior=current.data.automod_behavior,
        max_message_length=current.data.max_message_length,
        commands=["ban", "unban"],
    )
    assert response.data.commands is not None
    assert "ban" in response.data.commands
    assert "unban" in response.data.commands


def test_command_crud(client: Stream):
    """Full CRUD cycle for custom commands."""
    cmd_name = f"testcmd{uuid.uuid4().hex[:8]}"

    # create
    response = client.chat.create_command(description="My test command", name=cmd_name)
    assert response.data.command is not None
    assert response.data.command.name == cmd_name

    # get
    response = client.chat.get_command(name=cmd_name)
    assert response.data.name == cmd_name

    # update
    response = client.chat.update_command(name=cmd_name, description="Updated command")
    assert response.data.command is not None
    assert response.data.command.description == "Updated command"

    # list
    response = client.chat.list_commands()
    assert response.data.commands is not None
    cmd_names = [c.name for c in response.data.commands]
    assert cmd_name in cmd_names

    # delete
    client.chat.delete_command(name=cmd_name)


def test_query_threads(client: Stream, channel: Channel, random_user):
    """Create a thread and query threads."""
    parent = channel.send_message(
        message=MessageRequest(text="thread parent", user_id=random_user.id)
    )
    parent_id = parent.data.message.id

    channel.send_message(
        message=MessageRequest(
            text="thread reply",
            user_id=random_user.id,
            parent_id=parent_id,
        )
    )

    response = client.chat.query_threads(user_id=random_user.id)
    assert response.data.threads is not None
    assert len(response.data.threads) >= 1


def test_query_threads_with_options(client: Stream, channel: Channel, random_user):
    """Query threads with limit, filter, and sort options."""
    for i in range(3):
        parent = channel.send_message(
            message=MessageRequest(text=f"thread parent {i}", user_id=random_user.id)
        )
        channel.send_message(
            message=MessageRequest(
                text=f"thread reply {i}",
                user_id=random_user.id,
                parent_id=parent.data.message.id,
            )
        )

    cid = f"{channel.channel_type}:{channel.channel_id}"
    response = client.chat.query_threads(
        filter={"channel_cid": cid},
        sort=[SortParamRequest(field="created_at", direction=-1)],
        limit=1,
        user_id=random_user.id,
    )
    assert response.data.threads is not None
    assert len(response.data.threads) == 1
    assert response.data.next is not None


def test_permissions_roles(client: Stream):
    """Create and delete a custom role."""
    role_name = f"testrole{uuid.uuid4().hex[:8]}"

    client.create_role(name=role_name)
    time.sleep(2)

    response = client.list_roles()
    assert response.data.roles is not None
    role_names = [r.name for r in response.data.roles]
    assert role_name in role_names

    client.delete_role(name=role_name)
    time.sleep(2)

    response = client.list_roles()
    role_names = [r.name for r in response.data.roles]
    assert role_name not in role_names


def test_list_get_permission(client: Stream):
    """List permissions and get a specific one."""
    response = client.list_permissions()
    assert response.data.permissions is not None
    assert len(response.data.permissions) > 0

    response = client.get_permission(id="create-channel")
    assert response.data.permission is not None
    assert response.data.permission.id == "create-channel"


def test_check_push(client: Stream, channel: Channel, random_user):
    """Check push notification rendering."""
    msg = channel.send_message(
        message=MessageRequest(text="/giphy wave", user_id=random_user.id)
    )
    response = client.check_push(
        message_id=msg.data.message.id,
        skip_devices=True,
        user_id=random_user.id,
    )
    assert response.data.rendered_message is not None


def test_check_sqs(client: Stream):
    """Check SQS configuration (expected to fail with invalid creds)."""
    response = client.check_sqs(
        sqs_key="key", sqs_secret="secret", sqs_url="https://foo.com/bar"
    )
    assert response.data.status == "error"


def test_check_sns(client: Stream):
    """Check SNS configuration (expected to fail with invalid creds)."""
    response = client.check_sns(
        sns_key="key",
        sns_secret="secret",
        sns_topic_arn="arn:aws:sns:us-east-1:123456789012:sns-topic",
    )
    assert response.data.status == "error"


def test_get_rate_limits(client: Stream):
    """Get rate limit information."""
    response = client.get_rate_limits()
    assert response.data.server_side is not None

    response = client.get_rate_limits(server_side=True, android=True)
    assert response.data.server_side is not None
    assert response.data.android is not None


def test_response_metadata(client: Stream):
    """Verify StreamResponse contains metadata (headers, status_code, rate_limit)."""
    response = client.get_app()
    assert response.status_code() == 200
    assert len(response.headers()) > 0
    rate_limit = response.rate_limit()
    assert rate_limit is not None
    assert rate_limit.limit > 0
    assert rate_limit.remaining >= 0


def test_auth_exception(client: Stream):
    """Verify authentication failure raises StreamAPIException."""
    bad_client = Stream(api_key="bad", api_secret="guy")
    with pytest.raises(StreamAPIException):
        bad_client.chat.get_channel_type(name="team")


def test_imports_end2end(client: Stream):
    """End-to-end import: create URL, create import, get import, list imports."""
    import requests

    url_resp = client.create_import_url(filename=str(uuid.uuid4()) + ".json")
    assert url_resp.data.upload_url is not None
    assert url_resp.data.path is not None

    upload_resp = requests.put(
        url_resp.data.upload_url,
        data=b"{}",
        headers={"Content-Type": "application/json"},
    )
    assert upload_resp.status_code == 200

    create_resp = client.create_import(path=url_resp.data.path, mode="upsert")
    assert create_resp.data.import_task is not None
    assert create_resp.data.import_task.id is not None

    get_resp = client.get_import(id=create_resp.data.import_task.id)
    assert get_resp.data.import_task is not None
    assert get_resp.data.import_task.id == create_resp.data.import_task.id

    list_resp = client.list_imports()
    assert list_resp.data.import_tasks is not None
    assert len(list_resp.data.import_tasks) >= 1
