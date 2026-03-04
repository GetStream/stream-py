"""
Verify that the code snippets from the Python quickstart docs actually work.
Each test corresponds to a code block in:
  docs-content/chat/python/01-quick_start/01-backend_quickstart.md
"""

import uuid

from getstream import Stream
from getstream.chat.channel import Channel
from getstream.models import (
    Attachment,
    ChannelInput,
    ChannelInputRequest,
    ChannelMemberRequest,
    MessageRequest,
    QueryUsersPayload,
    UserRequest,
)


def test_quickstart_block1_client_init_and_token(client: Stream):
    """Block 1: Client instantiation + token creation."""
    token = client.create_token("john")
    assert token is not None
    assert isinstance(token, str)
    assert len(token) > 0


def test_quickstart_block2_upsert_user(client: Stream):
    """Block 2: Upsert a user."""
    user_id = f"docs-test-{uuid.uuid4()}"

    client.upsert_users(
        UserRequest(id=user_id, role="admin", custom={"mycustomfield": "123"})
    )

    # verify user was created
    resp = client.query_users(
        QueryUsersPayload(filter_conditions={"id": {"$eq": user_id}})
    )
    assert len(resp.data.users) == 1
    assert resp.data.users[0].role == "admin"
    assert resp.data.users[0].custom.get("mycustomfield") == "123"

    # cleanup
    client.delete_users(user_ids=[user_id], user="hard")


def test_quickstart_block3_create_and_update_channel(client: Stream, random_user):
    """Block 3: Create channel + update it."""
    user_id = random_user.id
    channel_id = f"docs-test-{uuid.uuid4()}"

    channel = client.chat.channel("messaging", channel_id)
    resp = channel.get_or_create(data=ChannelInput(created_by_id=user_id))
    assert resp.data.channel is not None
    assert resp.data.channel.type == "messaging"

    # update channel
    resp = channel.update(
        data=ChannelInputRequest(
            custom={
                "name": "my channel",
                "image": "image url",
                "mycustomfield": "123",
            }
        )
    )
    assert resp.data.channel is not None
    assert resp.data.channel.custom.get("name") == "my channel"
    assert resp.data.channel.custom.get("mycustomfield") == "123"

    # cleanup
    client.chat.delete_channels(
        cids=[f"messaging:{channel_id}"], hard_delete=True
    )


def test_quickstart_block4_add_remove_members_moderators(
    client: Stream, random_users, channel: Channel
):
    """Block 4: Add/remove members and moderators."""
    user_ids = [u.id for u in random_users[:3]]

    # add members
    resp = channel.update(
        add_members=[ChannelMemberRequest(user_id=uid) for uid in user_ids]
    )
    assert resp.data.members is not None
    member_ids = {m.user_id for m in resp.data.members}
    for uid in user_ids:
        assert uid in member_ids

    # remove one member
    resp = channel.update(remove_members=[user_ids[2]])
    member_ids = {m.user_id for m in resp.data.members}
    assert user_ids[2] not in member_ids

    # add moderator
    resp = channel.update(add_moderators=[user_ids[0]])
    mod = next(m for m in resp.data.members if m.user_id == user_ids[0])
    assert mod.channel_role == "channel_moderator"

    # demote moderator
    resp = channel.update(demote_moderators=[user_ids[0]])
    mod = next(m for m in resp.data.members if m.user_id == user_ids[0])
    assert mod.channel_role == "channel_member"


def test_quickstart_block5_send_message(
    client: Stream, random_user, channel: Channel
):
    """Block 5: Send a message with attachments."""
    josh_id = random_user.id

    resp = channel.send_message(
        MessageRequest(
            text="@Josh I told them I was pesca-pescatarian. Which is one who eats solely fish who eat other fish.",
            attachments=[
                Attachment(
                    type="image",
                    asset_url="https://bit.ly/2K74TaG",
                    thumb_url="https://bit.ly/2Uumxti",
                    custom={"myCustomField": 123},
                )
            ],
            mentioned_users=[josh_id],
            user_id=josh_id,
            custom={"anotherCustomField": 234},
        )
    )
    assert resp.data.message is not None
    assert "pesca-pescatarian" in resp.data.message.text
    assert len(resp.data.message.attachments) == 1
    assert resp.data.message.attachments[0].type == "image"
    assert resp.data.message.custom.get("anotherCustomField") == 234
