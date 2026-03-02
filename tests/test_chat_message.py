import time
import uuid

import pytest

from getstream import Stream
from getstream.base import StreamAPIException
from getstream.chat.channel import Channel
from getstream.models import (
    ChannelInput,
    ChannelMemberRequest,
    DeliveredMessagePayload,
    EventRequest,
    MessageRequest,
    ReactionRequest,
    SearchPayload,
    SortParamRequest,
)


def test_send_message(channel: Channel, random_user):
    """Send a message with skip_push option."""
    response = channel.send_message(
        message=MessageRequest(text="hi", user_id=random_user.id),
        skip_push=True,
    )
    assert response.data.message is not None
    assert response.data.message.text == "hi"


def test_send_pending_message(client: Stream, channel: Channel, random_user):
    """Send a pending message and commit it."""
    response = channel.send_message(
        message=MessageRequest(text="hi", user_id=random_user.id),
        pending=True,
        pending_message_metadata={"extra_data": "test"},
    )
    assert response.data.message is not None
    assert response.data.message.text == "hi"

    commit_response = client.chat.commit_message(id=response.data.message.id)
    assert commit_response.data.message is not None
    assert commit_response.data.message.text == "hi"


def test_send_message_restricted_visibility(channel: Channel, random_users):
    """Send a message with restricted visibility."""
    amy = random_users[0].id
    paul = random_users[1].id
    sender = random_users[2].id

    channel.update(
        add_members=[ChannelMemberRequest(user_id=uid) for uid in [amy, paul, sender]]
    )

    response = channel.send_message(
        message=MessageRequest(
            text="hi",
            user_id=sender,
            restricted_visibility=[amy, paul],
        )
    )
    assert response.data.message is not None
    assert response.data.message.text == "hi"
    assert response.data.message.restricted_visibility == [amy, paul]


def test_get_message(client: Stream, channel: Channel, random_user):
    """Get a message by ID, including deleted messages."""
    msg_id = str(uuid.uuid4())
    channel.send_message(
        message=MessageRequest(id=msg_id, text="helloworld", user_id=random_user.id)
    )

    response = client.chat.get_message(id=msg_id)
    assert response.data.message is not None
    assert response.data.message.id == msg_id
    assert response.data.message.text == "helloworld"

    # delete and then retrieve with show_deleted_message
    client.chat.delete_message(id=msg_id)
    response = client.chat.get_message(id=msg_id, show_deleted_message=True)
    assert response.data.message is not None
    assert response.data.message.text == "helloworld"


def test_get_many_messages(channel: Channel, random_user):
    """Get multiple messages by IDs."""
    msg_id = str(uuid.uuid4())
    channel.send_message(
        message=MessageRequest(id=msg_id, text="helloworld", user_id=random_user.id)
    )
    response = channel.get_many_messages(ids=[msg_id])
    assert response.data.messages is not None
    assert len(response.data.messages) == 1


def test_update_message(client: Stream, channel: Channel, random_user):
    """Update a message's text."""
    msg_id = str(uuid.uuid4())
    response = channel.send_message(
        message=MessageRequest(id=msg_id, text="hello world", user_id=random_user.id)
    )
    assert response.data.message.text == "hello world"

    response = client.chat.update_message(
        id=msg_id,
        message=MessageRequest(text="helloworld", user_id=random_user.id),
    )
    assert response.data.message.text == "helloworld"


def test_update_message_partial(client: Stream, channel: Channel, random_user):
    """Partial update of a message."""
    msg_id = str(uuid.uuid4())
    channel.send_message(
        message=MessageRequest(id=msg_id, text="hello world", user_id=random_user.id)
    )
    response = client.chat.update_message_partial(
        id=msg_id,
        set={"text": "helloworld"},
        user_id=random_user.id,
    )
    assert response.data.message is not None
    assert response.data.message.text == "helloworld"


def test_delete_message(client: Stream, channel: Channel, random_user):
    """Delete a message (soft and hard)."""
    msg_id = str(uuid.uuid4())
    channel.send_message(
        message=MessageRequest(id=msg_id, text="helloworld", user_id=random_user.id)
    )
    response = client.chat.delete_message(id=msg_id)
    assert response.data.message is not None

    # hard delete
    msg_id2 = str(uuid.uuid4())
    channel.send_message(
        message=MessageRequest(id=msg_id2, text="helloworld", user_id=random_user.id)
    )
    response = client.chat.delete_message(id=msg_id2, hard=True)
    assert response.data.message is not None


def test_pin_unpin_message(client: Stream, channel: Channel, random_user):
    """Pin and unpin a message."""
    msg_id = str(uuid.uuid4())
    channel.send_message(
        message=MessageRequest(id=msg_id, text="hello world", user_id=random_user.id)
    )

    # pin
    response = client.chat.update_message_partial(
        id=msg_id,
        set={"pinned": True, "pin_expires": None},
        user_id=random_user.id,
    )
    assert response.data.message.pinned is True
    assert response.data.message.pinned_at is not None
    assert response.data.message.pinned_by is not None
    assert response.data.message.pinned_by.id == random_user.id

    # unpin
    response = client.chat.update_message_partial(
        id=msg_id,
        set={"pinned": False},
        user_id=random_user.id,
    )
    assert response.data.message.pinned is False


def test_get_replies(client: Stream, channel: Channel, random_user):
    """Send replies to a parent message and get them."""
    parent = channel.send_message(
        message=MessageRequest(text="parent", user_id=random_user.id)
    )
    parent_id = parent.data.message.id

    response = client.chat.get_replies(parent_id=parent_id)
    assert response.data.messages is not None
    assert len(response.data.messages) == 0

    for i in range(3):
        channel.send_message(
            message=MessageRequest(
                text=f"reply {i}",
                user_id=random_user.id,
                parent_id=parent_id,
            )
        )

    response = client.chat.get_replies(parent_id=parent_id)
    assert len(response.data.messages) == 3


def test_send_reaction(client: Stream, channel: Channel, random_user):
    """Send a reaction to a message."""
    msg = channel.send_message(
        message=MessageRequest(text="hi", user_id=random_user.id)
    )
    response = client.chat.send_reaction(
        id=msg.data.message.id,
        reaction=ReactionRequest(type="love", user_id=random_user.id),
    )
    assert response.data.message is not None
    assert len(response.data.message.latest_reactions) == 1
    assert response.data.message.latest_reactions[0].type == "love"


def test_delete_reaction(client: Stream, channel: Channel, random_user):
    """Delete a reaction from a message."""
    msg = channel.send_message(
        message=MessageRequest(text="hi", user_id=random_user.id)
    )
    client.chat.send_reaction(
        id=msg.data.message.id,
        reaction=ReactionRequest(type="love", user_id=random_user.id),
    )
    response = client.chat.delete_reaction(
        id=msg.data.message.id, type="love", user_id=random_user.id
    )
    assert response.data.message is not None
    assert len(response.data.message.latest_reactions) == 0


def test_get_reactions(client: Stream, channel: Channel, random_user):
    """Get reactions on a message."""
    msg = channel.send_message(
        message=MessageRequest(text="hi", user_id=random_user.id)
    )
    msg_id = msg.data.message.id

    response = client.chat.get_reactions(id=msg_id)
    assert response.data.reactions is not None
    assert len(response.data.reactions) == 0

    client.chat.send_reaction(
        id=msg_id,
        reaction=ReactionRequest(type="love", user_id=random_user.id),
    )
    client.chat.send_reaction(
        id=msg_id,
        reaction=ReactionRequest(type="clap", user_id=random_user.id),
    )

    response = client.chat.get_reactions(id=msg_id)
    assert len(response.data.reactions) == 2


def test_send_event(channel: Channel, random_user):
    """Send a typing event on a channel."""
    response = channel.send_event(
        event=EventRequest(type="typing.start", user_id=random_user.id)
    )
    assert response.data.event is not None
    assert response.data.event.type == "typing.start"


def test_translate_message(client: Stream, channel: Channel, random_user):
    """Translate a message."""
    msg_id = str(uuid.uuid4())
    channel.send_message(
        message=MessageRequest(id=msg_id, text="hello world", user_id=random_user.id)
    )
    response = client.chat.translate_message(id=msg_id, language="hu")
    assert response.data.message is not None


def test_run_message_action(client: Stream, channel: Channel, random_user):
    """Run a message action (e.g. giphy shuffle)."""
    msg_id = str(uuid.uuid4())
    channel.send_message(
        message=MessageRequest(id=msg_id, text="/giphy wave", user_id=random_user.id)
    )
    try:
        client.chat.run_message_action(
            id=msg_id,
            form_data={"image_action": "shuffle"},
            user_id=random_user.id,
        )
    except Exception:
        # giphy may not be configured on every test app
        pass


def test_query_message_history(client: Stream, channel: Channel, random_user):
    """Query message edit history."""
    msg_id = str(uuid.uuid4())
    channel.send_message(
        message=MessageRequest(id=msg_id, text="helloworld", user_id=random_user.id)
    )
    for i in range(1, 4):
        client.chat.update_message(
            id=msg_id,
            message=MessageRequest(text=f"helloworld-{i}", user_id=random_user.id),
        )

    response = client.chat.query_message_history(
        filter={"message_id": {"$eq": msg_id}},
        sort=[SortParamRequest(field="message_updated_at", direction=-1)],
        limit=1,
    )
    assert response.data.message_history is not None
    assert len(response.data.message_history) == 1
    assert response.data.message_history[0].text == "helloworld-2"


def test_search(client: Stream, channel: Channel, random_user):
    """Search messages across channels."""
    query = f"supercalifragilisticexpialidocious-{uuid.uuid4()}"
    channel.send_message(
        message=MessageRequest(
            text=f"How many syllables are there in {query}?",
            user_id=random_user.id,
        )
    )
    time.sleep(1)  # wait for indexing

    response = client.chat.search(
        payload=SearchPayload(
            filter_conditions={"type": "messaging"},
            query=query,
            limit=2,
            offset=0,
        )
    )
    assert response.data.results is not None
    assert len(response.data.results) >= 1
    assert query in response.data.results[0].message.text


def test_search_with_sort(client: Stream, channel: Channel, random_user):
    """Search messages with sort and cursor-based pagination."""
    text = f"searchsort-{uuid.uuid4()}"
    ids = [f"0{text}", f"1{text}"]
    channel.send_message(
        message=MessageRequest(id=ids[0], text=text, user_id=random_user.id)
    )
    channel.send_message(
        message=MessageRequest(id=ids[1], text=text, user_id=random_user.id)
    )
    time.sleep(1)  # wait for indexing

    response = client.chat.search(
        payload=SearchPayload(
            filter_conditions={"type": "messaging"},
            query=text,
            limit=1,
            sort=[SortParamRequest(field="created_at", direction=-1)],
        )
    )
    assert response.data.results is not None
    assert len(response.data.results) >= 1
    assert response.data.results[0].message.id == ids[1]
    assert response.data.next is not None

    # fetch next page
    response2 = client.chat.search(
        payload=SearchPayload(
            filter_conditions={"type": "messaging"},
            query=text,
            limit=1,
            next=response.data.next,
            sort=[SortParamRequest(field="created_at", direction=-1)],
        )
    )
    assert response2.data.results is not None
    assert len(response2.data.results) >= 1
    assert response2.data.results[0].message.id == ids[0]


def test_search_message_filters(client: Stream, channel: Channel, random_user):
    """Search messages using message_filter_conditions."""
    query = f"supercalifragilisticexpialidocious-{uuid.uuid4()}"
    channel.send_message(
        message=MessageRequest(
            text=f"How many syllables are there in {query}?",
            user_id=random_user.id,
        )
    )
    channel.send_message(
        message=MessageRequest(
            text="Does 'cious' count as one or two?",
            user_id=random_user.id,
        )
    )
    time.sleep(1)  # wait for indexing

    response = client.chat.search(
        payload=SearchPayload(
            filter_conditions={"type": "messaging"},
            message_filter_conditions={"text": {"$q": query}},
            limit=2,
            offset=0,
        )
    )
    assert response.data.results is not None
    assert len(response.data.results) >= 1
    assert query in response.data.results[0].message.text


def test_delete_message_for_me(client: Stream, channel: Channel, random_user):
    """Delete a message for a specific user (delete for me)."""
    channel.update(add_members=[ChannelMemberRequest(user_id=random_user.id)])
    msg_id = str(uuid.uuid4())
    channel.send_message(
        message=MessageRequest(id=msg_id, text="helloworld", user_id=random_user.id)
    )
    response = client.chat.delete_message(
        id=msg_id, delete_for_me=True, deleted_by=random_user.id
    )
    assert response.data.message is not None


def test_mark_delivered(client: Stream, channel: Channel, random_user):
    """Mark messages as delivered."""
    cid = f"{channel.channel_type}:{channel.channel_id}"
    response = client.chat.mark_delivered(
        user_id=random_user.id,
        latest_delivered_messages=[
            DeliveredMessagePayload(cid=cid, id="test-message-id")
        ],
    )
    assert response is not None


def test_silent_message(channel: Channel, random_user):
    """Send a silent message."""
    response = channel.send_message(
        message=MessageRequest(
            text="This is a silent message", user_id=random_user.id, silent=True
        ),
    )
    assert response.data.message is not None
    assert response.data.message.silent is True


def test_skip_enrich_url(client: Stream, channel: Channel, random_user):
    """Send a message with a URL but skip enrichment."""
    response = channel.send_message(
        message=MessageRequest(
            text="Check out https://getstream.io for more info",
            user_id=random_user.id,
        ),
        skip_enrich_url=True,
    )
    assert response.data.message is not None
    assert len(response.data.message.attachments) == 0


def test_keep_channel_hidden(client: Stream, channel: Channel, random_user):
    """Send a message keeping the channel hidden."""
    channel.update(add_members=[ChannelMemberRequest(user_id=random_user.id)])

    # hide the channel
    channel.hide(user_id=random_user.id)

    # send message with keep_channel_hidden
    channel.send_message(
        message=MessageRequest(text="Hidden message", user_id=random_user.id),
        keep_channel_hidden=True,
    )

    # channel should still be hidden
    cid = f"{channel.channel_type}:{channel.channel_id}"
    q_resp = client.chat.query_channels(
        filter_conditions={"cid": cid}, user_id=random_user.id
    )
    assert len(q_resp.data.channels) == 0

    # show it back for cleanup
    channel.show(user_id=random_user.id)


def test_undelete_message(client: Stream, channel: Channel, random_user):
    """Soft delete and then undelete a message."""
    msg_id = str(uuid.uuid4())
    channel.send_message(
        message=MessageRequest(
            id=msg_id, text="Message to undelete", user_id=random_user.id
        )
    )

    # soft delete
    client.chat.delete_message(id=msg_id)
    get_resp = client.chat.get_message(id=msg_id)
    assert get_resp.data.message.type == "deleted"

    # undelete
    undelete_resp = client.chat.undelete_message(id=msg_id, undeleted_by=random_user.id)
    assert undelete_resp.data.message is not None
    assert undelete_resp.data.message.type != "deleted"
    assert undelete_resp.data.message.text == "Message to undelete"


def test_pin_expiration(client: Stream, channel: Channel, random_user):
    """Pin a message with expiration."""
    msg_id = str(uuid.uuid4())
    channel.send_message(
        message=MessageRequest(
            id=msg_id, text="Message to pin with expiry", user_id=random_user.id
        )
    )

    # pin with short expiry
    from datetime import datetime, timedelta, timezone

    expiry = datetime.now(timezone.utc) + timedelta(seconds=3)
    response = client.chat.update_message_partial(
        id=msg_id,
        set={"pinned": True, "pin_expires": expiry.isoformat()},
        user_id=random_user.id,
    )
    assert response.data.message.pinned is True

    # wait for expiry
    time.sleep(4)

    get_resp = client.chat.get_message(id=msg_id)
    assert get_resp.data.message.pinned is False


def test_system_message(channel: Channel, random_user):
    """Send a system message."""
    response = channel.send_message(
        message=MessageRequest(
            text="User joined the channel",
            user_id=random_user.id,
            type="system",
        ),
    )
    assert response.data.message is not None
    assert response.data.message.type == "system"


def test_channel_role_in_member(client: Stream, random_users):
    """Verify channel_role is present in message member."""
    member_id = random_users[0].id
    mod_id = random_users[1].id

    channel_id = str(uuid.uuid4())
    ch = client.chat.channel("messaging", channel_id)
    ch.get_or_create(
        data=ChannelInput(
            created_by_id=member_id,
            members=[
                ChannelMemberRequest(user_id=member_id, channel_role="channel_member"),
                ChannelMemberRequest(user_id=mod_id, channel_role="channel_moderator"),
            ],
        )
    )

    resp_member = ch.send_message(
        message=MessageRequest(text="message from member", user_id=member_id)
    )
    assert resp_member.data.message.member is not None
    assert resp_member.data.message.member.channel_role == "channel_member"

    resp_mod = ch.send_message(
        message=MessageRequest(text="message from moderator", user_id=mod_id)
    )
    assert resp_mod.data.message.member is not None
    assert resp_mod.data.message.member.channel_role == "channel_moderator"

    try:
        client.chat.delete_channels(cids=[f"messaging:{channel_id}"], hard_delete=True)
    except Exception:
        pass


def test_query_reactions(client: Stream, channel: Channel, random_users):
    """Query reactions on a message."""
    msg = channel.send_message(
        message=MessageRequest(
            text="Message for query reactions", user_id=random_users[0].id
        )
    )
    msg_id = msg.data.message.id

    client.chat.send_reaction(
        id=msg_id,
        reaction=ReactionRequest(type="like", user_id=random_users[0].id),
    )
    client.chat.send_reaction(
        id=msg_id,
        reaction=ReactionRequest(type="wow", user_id=random_users[1].id),
    )

    response = client.chat.query_reactions(id=msg_id)
    assert response.data.reactions is not None
    assert len(response.data.reactions) >= 2


def test_enforce_unique_reaction(client: Stream, channel: Channel, random_user):
    """Enforce unique reaction per user."""
    msg = channel.send_message(
        message=MessageRequest(
            text="Message for unique reaction", user_id=random_user.id
        )
    )
    msg_id = msg.data.message.id

    # send first reaction
    client.chat.send_reaction(
        id=msg_id,
        reaction=ReactionRequest(type="like", user_id=random_user.id),
        enforce_unique=True,
    )

    # send second reaction with enforce_unique — should replace
    client.chat.send_reaction(
        id=msg_id,
        reaction=ReactionRequest(type="love", user_id=random_user.id),
        enforce_unique=True,
    )

    # user should only have one reaction
    response = client.chat.get_reactions(id=msg_id)
    user_reactions = [r for r in response.data.reactions if r.user_id == random_user.id]
    assert len(user_reactions) == 1


def test_query_message_history_sort(client: Stream, channel: Channel, random_user):
    """Query message history with ascending sort by message_updated_at."""
    msg_id = str(uuid.uuid4())
    channel.send_message(
        message=MessageRequest(id=msg_id, text="sort initial", user_id=random_user.id)
    )

    client.chat.update_message(
        id=msg_id,
        message=MessageRequest(text="sort updated 1", user_id=random_user.id),
    )
    client.chat.update_message(
        id=msg_id,
        message=MessageRequest(text="sort updated 2", user_id=random_user.id),
    )

    # Query with ascending sort by message_updated_at
    try:
        response = client.chat.query_message_history(
            filter={"message_id": msg_id},
            sort=[SortParamRequest(field="message_updated_at", direction=1)],
        )
    except Exception as e:
        if "feature flag" in str(e) or "not enabled" in str(e):
            pytest.skip("QueryMessageHistory feature not enabled for this app")
        raise

    assert response.data.message_history is not None
    assert len(response.data.message_history) >= 2

    # Ascending: oldest first
    assert response.data.message_history[0].text == "sort initial"
    assert response.data.message_history[0].message_updated_by_id == random_user.id


def test_pending_false(client: Stream, channel: Channel, random_user):
    """Send a message with pending=False and verify it's immediately available."""
    response = channel.send_message(
        message=MessageRequest(text="Non-pending message", user_id=random_user.id),
        pending=False,
    )
    assert response.data.message is not None

    # Get the message to verify it's immediately available (no commit needed)
    get_response = client.chat.get_message(id=response.data.message.id)
    assert get_response.data.message is not None
    assert get_response.data.message.text == "Non-pending message"


def test_search_query_and_message_filters_error(client: Stream, random_user):
    """Using both query and message_filter_conditions together should error."""
    with pytest.raises(StreamAPIException):
        client.chat.search(
            payload=SearchPayload(
                filter_conditions={"members": {"$in": [random_user.id]}},
                query="test",
                message_filter_conditions={"text": {"$q": "test"}},
            )
        )


def test_search_offset_and_sort_error(client: Stream, random_user):
    """Using offset with sort should error."""
    with pytest.raises(StreamAPIException):
        client.chat.search(
            payload=SearchPayload(
                filter_conditions={"members": {"$in": [random_user.id]}},
                query="test",
                offset=1,
                sort=[SortParamRequest(field="created_at", direction=-1)],
            )
        )


def test_search_offset_and_next_error(client: Stream, random_user):
    """Using offset with next should error."""
    with pytest.raises(StreamAPIException):
        client.chat.search(
            payload=SearchPayload(
                filter_conditions={"members": {"$in": [random_user.id]}},
                query="test",
                offset=1,
                next="some_next_token",
            )
        )
