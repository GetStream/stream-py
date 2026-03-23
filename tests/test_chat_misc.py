import time
import uuid

import pytest

from getstream import Stream
from getstream.base import StreamAPIException
from getstream.chat.channel import Channel
from getstream.models import (
    AsyncModerationCallbackConfig,
    ChannelInput,
    ChannelMemberRequest,
    EventHook,
    FileUploadConfig,
    MessageRequest,
    QueryFutureChannelBansPayload,
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
    original_commands = [c.name for c in (current.data.commands or [])]

    try:
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
    finally:
        client.chat.update_channel_type(
            name="team",
            automod=current.data.automod,
            automod_behavior=current.data.automod_behavior,
            max_message_length=current.data.max_message_length,
            commands=original_commands,
        )


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


@pytest.mark.skip(reason="slow and flaky due to waits")
def test_permissions_roles(client: Stream):
    """Create and delete a custom role."""
    role_name = f"testrole{uuid.uuid4().hex[:8]}"

    client.create_role(name=role_name)

    # Poll until role appears (eventual consistency)
    for _ in range(10):
        response = client.list_roles()
        assert response.data.roles is not None
        role_names = [r.name for r in response.data.roles]
        if role_name in role_names:
            break
        time.sleep(1)
    else:
        raise AssertionError(f"Role {role_name} did not appear within timeout")

    client.delete_role(name=role_name)

    # Poll until role disappears
    for _ in range(10):
        response = client.list_roles()
        role_names = [r.name for r in response.data.roles]
        if role_name not in role_names:
            break
        time.sleep(1)
    else:
        raise AssertionError(f"Role {role_name} was not deleted within timeout")


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


def test_file_upload_config(client: Stream):
    """Set and verify file upload configuration."""
    # save original config
    original = client.get_app()
    original_config = original.data.app.file_upload_config

    try:
        client.update_app(
            file_upload_config=FileUploadConfig(
                size_limit=10 * 1024 * 1024,
                allowed_file_extensions=[".pdf", ".doc", ".txt"],
                allowed_mime_types=["application/pdf", "text/plain"],
            )
        )

        verify = client.get_app()
        cfg = verify.data.app.file_upload_config
        assert cfg.size_limit == 10 * 1024 * 1024
        assert cfg.allowed_file_extensions == [".pdf", ".doc", ".txt"]
        assert cfg.allowed_mime_types == ["application/pdf", "text/plain"]
    finally:
        # restore original config
        if original_config is not None:
            client.update_app(file_upload_config=original_config)


def test_query_future_channel_bans(client: Stream, random_users):
    """Query future channel bans."""
    creator = random_users[0]
    target = random_users[1]

    channel_id = str(uuid.uuid4())
    ch = client.chat.channel("messaging", channel_id)
    ch.get_or_create(
        data=ChannelInput(
            created_by_id=creator.id,
            members=[
                ChannelMemberRequest(user_id=creator.id),
                ChannelMemberRequest(user_id=target.id),
            ],
        )
    )
    cid = f"messaging:{channel_id}"

    client.moderation.ban(
        target_user_id=target.id,
        banned_by_id=creator.id,
        channel_cid=cid,
        reason="test future ban query",
    )

    try:
        response = client.chat.query_future_channel_bans(
            payload=QueryFutureChannelBansPayload(user_id=creator.id)
        )
        assert response.data.bans is not None
    finally:
        client.moderation.unban(
            target_user_id=target.id,
            channel_cid=cid,
        )
        try:
            client.chat.delete_channels(cids=[cid], hard_delete=True)
        except Exception:
            pass


def test_create_channel_type(client: Stream):
    """Create a channel type with custom settings."""
    type_name = f"testtype{uuid.uuid4().hex[:8]}"

    try:
        response = client.chat.create_channel_type(
            name=type_name,
            automod="disabled",
            automod_behavior="flag",
            max_message_length=5000,
        )
        assert response.data.name == type_name
        assert response.data.max_message_length == 5000

        # Channel types are eventually consistent
        time.sleep(6)
    finally:
        # Clean up
        try:
            client.chat.delete_channel_type(name=type_name)
        except Exception:
            pass


def test_update_channel_type_mark_messages_pending(client: Stream):
    """Update a channel type with mark_messages_pending=True."""
    type_name = f"testtype{uuid.uuid4().hex[:8]}"

    try:
        client.chat.create_channel_type(
            name=type_name,
            automod="disabled",
            automod_behavior="flag",
            max_message_length=5000,
        )
        time.sleep(6)

        response = client.chat.update_channel_type(
            name=type_name,
            automod="disabled",
            automod_behavior="flag",
            max_message_length=5000,
            mark_messages_pending=True,
        )
        assert response.data.mark_messages_pending is True

        # Verify via get
        get_response = client.chat.get_channel_type(name=type_name)
        assert get_response.data.mark_messages_pending is True
    finally:
        try:
            client.chat.delete_channel_type(name=type_name)
        except Exception:
            pass


def test_update_channel_type_push_notifications(client: Stream):
    """Update a channel type with push_notifications=False."""
    type_name = f"testtype{uuid.uuid4().hex[:8]}"

    try:
        client.chat.create_channel_type(
            name=type_name,
            automod="disabled",
            automod_behavior="flag",
            max_message_length=5000,
        )
        time.sleep(6)

        response = client.chat.update_channel_type(
            name=type_name,
            automod="disabled",
            automod_behavior="flag",
            max_message_length=5000,
            push_notifications=False,
        )
        assert response.data.push_notifications is False

        # Verify via get
        get_response = client.chat.get_channel_type(name=type_name)
        assert get_response.data.push_notifications is False
    finally:
        try:
            client.chat.delete_channel_type(name=type_name)
        except Exception:
            pass


def test_delete_channel_type(client: Stream):
    """Create and delete a channel type with retry."""
    type_name = f"testdeltype{uuid.uuid4().hex[:8]}"

    client.chat.create_channel_type(
        name=type_name,
        automod="disabled",
        automod_behavior="flag",
        max_message_length=5000,
    )
    time.sleep(6)

    # Retry delete up to 5 times (eventual consistency)
    delete_err = None
    for _ in range(5):
        try:
            client.chat.delete_channel_type(name=type_name)
            delete_err = None
            break
        except Exception as e:
            delete_err = e
            time.sleep(1)

    assert delete_err is None, f"Failed to delete channel type: {delete_err}"


def test_get_thread(client: Stream, channel: Channel, random_user):
    """Get a thread with reply_limit and verify replies."""
    parent = channel.send_message(
        message=MessageRequest(text="thread parent", user_id=random_user.id)
    )
    parent_id = parent.data.message.id

    # Send 2 replies
    for i in range(2):
        channel.send_message(
            message=MessageRequest(
                text=f"thread reply {i}",
                user_id=random_user.id,
                parent_id=parent_id,
            )
        )

    response = client.chat.get_thread(message_id=parent_id, reply_limit=10)
    assert response.data.thread.parent_message_id == parent_id
    assert len(response.data.thread.latest_replies) >= 2


def test_get_rate_limits_specific_endpoints(client: Stream):
    """Get rate limits for specific endpoints."""
    response = client.get_rate_limits(
        server_side=True,
        android=True,
        endpoints="GetRateLimits,SendMessage",
    )
    assert len(response.data.android) == 2
    assert len(response.data.server_side) == 2

    for info in response.data.server_side.values():
        assert info.limit > 0
        assert info.remaining >= 0


def test_event_hooks_sqs_sns(client: Stream):
    """Test setting SQS, SNS, and pending_message event hooks."""
    # Save original hooks to restore later
    original = client.get_app()
    original_hooks = original.data.app.event_hooks

    try:
        # SQS event hook
        client.update_app(
            event_hooks=[
                EventHook(
                    hook_type="sqs",
                    enabled=True,
                    event_types=["message.new"],
                    sqs_queue_url="https://sqs.us-east-1.amazonaws.com/123456789012/my-queue",
                    sqs_region="us-east-1",
                    sqs_auth_type="keys",
                    sqs_key="some key",
                    sqs_secret="some secret",
                ),
            ]
        )

        # SNS event hook
        client.update_app(
            event_hooks=[
                EventHook(
                    hook_type="sns",
                    enabled=True,
                    event_types=["message.new"],
                    sns_topic_arn="arn:aws:sns:us-east-1:123456789012:my-topic",
                    sns_region="us-east-1",
                    sns_auth_type="keys",
                    sns_key="some key",
                    sns_secret="some secret",
                ),
            ]
        )

        # Pending message event hook with async moderation callback
        client.update_app(
            event_hooks=[
                EventHook(
                    hook_type="pending_message",
                    enabled=True,
                    webhook_url="https://example.com/pending",
                    timeout_ms=10000,
                    callback=AsyncModerationCallbackConfig(
                        mode="CALLBACK_MODE_REST",
                    ),
                ),
            ]
        )

        # Clear all hooks
        client.update_app(event_hooks=[])
        verify = client.get_app()
        assert len(verify.data.app.event_hooks or []) == 0
    finally:
        # Restore original hooks
        client.update_app(event_hooks=original_hooks or [])


def test_get_retention_policy(client: Stream):
    """Create a retention policy, then list all policies."""
    try:
        client.chat.set_retention_policy(policy="old-messages", max_age_hours=480)

        response = client.chat.get_retention_policy()
        assert response.data.policies is not None
        policies = [p.policy for p in response.data.policies]
        assert "old-messages" in policies
    finally:
        try:
            client.chat.delete_retention_policy(policy="old-messages")
        except Exception:
            pass


def test_get_retention_policy_runs(client: Stream):
    """Query retention policy run history."""
    try:
        # Ensure at least one policy exists so the endpoint works
        client.chat.set_retention_policy(policy="old-messages", max_age_hours=720)

        response = client.chat.get_retention_policy_runs(limit=10, offset=0)
        assert response.data.runs is not None
    finally:
        try:
            client.chat.delete_retention_policy(policy="old-messages")
        except Exception:
            pass
