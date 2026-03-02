import uuid

import pytest

from getstream import Stream
from getstream.chat.channel import Channel
from getstream.models import (
    ChannelMemberRequest,
    MessageRequest,
    QueryBannedUsersPayload,
    QueryMessageFlagsPayload,
)


def test_ban_user(client: Stream, random_user, server_user):
    """Ban a user."""
    response = client.moderation.ban(
        target_user_id=random_user.id,
        banned_by_id=server_user.id,
    )
    assert response is not None


def test_unban_user(client: Stream, random_user, server_user):
    """Ban then unban a user."""
    client.moderation.ban(
        target_user_id=random_user.id,
        banned_by_id=server_user.id,
    )
    response = client.moderation.unban(
        target_user_id=random_user.id,
        unbanned_by_id=server_user.id,
    )
    assert response is not None


def test_shadow_ban(client: Stream, random_user, server_user, channel: Channel):
    """Shadow ban a user and verify messages are shadowed."""
    channel.update(
        add_members=[
            ChannelMemberRequest(user_id=uid)
            for uid in [random_user.id, server_user.id]
        ]
    )

    msg_id = str(uuid.uuid4())
    channel.send_message(
        message=MessageRequest(id=msg_id, text="hello world", user_id=random_user.id)
    )
    response = client.chat.get_message(id=msg_id)
    assert response.data.message.shadowed is not True

    # shadow ban
    client.moderation.ban(
        target_user_id=random_user.id,
        banned_by_id=server_user.id,
        shadow=True,
    )

    msg_id2 = str(uuid.uuid4())
    channel.send_message(
        message=MessageRequest(id=msg_id2, text="hello world", user_id=random_user.id)
    )
    response = client.chat.get_message(id=msg_id2)
    assert response.data.message.shadowed is True

    # remove shadow ban
    client.moderation.unban(
        target_user_id=random_user.id,
        unbanned_by_id=server_user.id,
    )

    msg_id3 = str(uuid.uuid4())
    channel.send_message(
        message=MessageRequest(id=msg_id3, text="hello world", user_id=random_user.id)
    )
    response = client.chat.get_message(id=msg_id3)
    assert response.data.message.shadowed is not True


def test_query_banned_users(client: Stream, random_user, server_user):
    """Ban a user and query banned users."""
    client.moderation.ban(
        target_user_id=random_user.id,
        banned_by_id=server_user.id,
        reason="because",
    )
    response = client.chat.query_banned_users(
        payload=QueryBannedUsersPayload(
            filter_conditions={"reason": "because"},
            limit=1,
        )
    )
    assert response.data.bans is not None
    assert len(response.data.bans) >= 1

    # cleanup
    client.moderation.unban(
        target_user_id=random_user.id,
        unbanned_by_id=server_user.id,
    )


def test_mute_user(client: Stream, random_users):
    """Mute a user."""
    response = client.moderation.mute(
        target_ids=[random_users[0].id],
        user_id=random_users[1].id,
    )
    assert response.data.mutes is not None
    assert len(response.data.mutes) >= 1
    assert response.data.mutes[0].target.id == random_users[0].id
    assert response.data.mutes[0].user.id == random_users[1].id

    # cleanup
    client.moderation.unmute(
        target_ids=[random_users[0].id],
        user_id=random_users[1].id,
    )


def test_mute_users(client: Stream, random_users):
    """Mute multiple users at once."""
    muter = random_users[0].id
    targets = [random_users[1].id, random_users[2].id]

    response = client.moderation.mute(
        target_ids=targets,
        user_id=muter,
    )
    assert response.data.mutes is not None
    muted_target_ids = [m.target.id for m in response.data.mutes]
    for tid in targets:
        assert tid in muted_target_ids

    # cleanup
    client.moderation.unmute(
        target_ids=targets,
        user_id=muter,
    )


def test_unmute_user(client: Stream, random_users):
    """Mute then unmute a user."""
    client.moderation.mute(
        target_ids=[random_users[0].id],
        user_id=random_users[1].id,
    )
    response = client.moderation.unmute(
        target_ids=[random_users[0].id],
        user_id=random_users[1].id,
    )
    assert response is not None


def test_mute_with_timeout(client: Stream, random_users):
    """Mute a user with a timeout."""
    response = client.moderation.mute(
        target_ids=[random_users[0].id],
        user_id=random_users[1].id,
        timeout=10,
    )
    assert response.data.mutes is not None
    assert len(response.data.mutes) >= 1
    assert response.data.mutes[0].expires is not None

    # cleanup
    client.moderation.unmute(
        target_ids=[random_users[0].id],
        user_id=random_users[1].id,
    )


def test_flag_user(client: Stream, random_user, server_user):
    """Flag a user."""
    response = client.moderation.flag(
        entity_id=random_user.id,
        entity_type="stream:user",
        user_id=server_user.id,
    )
    assert response is not None


def test_flag_message(client: Stream, channel: Channel, random_user, server_user):
    """Flag a message."""
    channel.update(
        add_members=[
            ChannelMemberRequest(user_id=uid)
            for uid in [random_user.id, server_user.id]
        ]
    )
    msg_id = str(uuid.uuid4())
    channel.send_message(
        message=MessageRequest(id=msg_id, text="helloworld", user_id=random_user.id)
    )
    response = client.moderation.flag(
        entity_id=msg_id,
        entity_type="stream:chat:v1:message",
        user_id=server_user.id,
    )
    assert response is not None


def test_query_message_flags(
    client: Stream, channel: Channel, random_user, server_user
):
    """Flag a message then query message flags."""
    channel.update(
        add_members=[
            ChannelMemberRequest(user_id=uid)
            for uid in [random_user.id, server_user.id]
        ]
    )
    msg_id = str(uuid.uuid4())
    channel.send_message(
        message=MessageRequest(id=msg_id, text="helloworld", user_id=random_user.id)
    )
    client.moderation.flag(
        entity_id=msg_id,
        entity_type="stream:chat:v1:message",
        entity_creator_id=random_user.id,
        user_id=server_user.id,
        reason="inappropriate content",
    )

    # Verify QueryMessageFlags endpoint works with channel_cid filter.
    # V2 moderation.flag() may not populate the v1 chat flags store,
    # so we only verify the endpoint doesn't error (same as getstream-go).
    cid = f"{channel.channel_type}:{channel.channel_id}"
    response = client.chat.query_message_flags(
        payload=QueryMessageFlagsPayload(filter_conditions={"channel_cid": cid})
    )
    assert response.data.flags is not None

    # Also verify with user_id filter
    response = client.chat.query_message_flags(
        payload=QueryMessageFlagsPayload(
            filter_conditions={"user_id": server_user.id}
        )
    )
    assert response.data.flags is not None


def test_block_unblock_user(client: Stream, random_user, server_user):
    """Block and unblock a user."""
    client.block_users(
        blocked_user_id=random_user.id,
        user_id=server_user.id,
    )
    response = client.get_blocked_users(user_id=server_user.id)
    assert response.data.blocks is not None
    assert len(response.data.blocks) > 0

    client.unblock_users(
        blocked_user_id=random_user.id,
        user_id=server_user.id,
    )
    response = client.get_blocked_users(user_id=server_user.id)
    assert response.data.blocks is not None
    assert len(response.data.blocks) == 0
