import uuid

import pytest

from getstream import Stream
from getstream.base import StreamAPIException
from getstream.chat.channel import Channel
from getstream.models import (
    ChannelInput,
    ChannelMemberRequest,
    MessageRequest,
    Response,
    SortParamRequest,
)


def _create_draft(channel, text, user_id, parent_id=None):
    """Create a draft via raw HTTP (endpoint is client-side-only, not in generated SDK)."""
    message = {"text": text, "user_id": user_id}
    if parent_id:
        message["parent_id"] = parent_id
    return channel.client.post(
        "/api/v2/chat/channels/{type}/{id}/draft",
        Response,
        path_params={"type": channel.channel_type, "id": channel.channel_id},
        json={"message": message},
    )


class TestDrafts:
    def test_create_and_get_draft(self, channel: Channel, random_user):
        """Create a draft via raw HTTP and retrieve it via SDK."""
        text = f"draft-{uuid.uuid4()}"
        channel.update(add_members=[ChannelMemberRequest(user_id=random_user.id)])

        _create_draft(channel, text, random_user.id)

        response = channel.get_draft(user_id=random_user.id)
        assert response.data.draft is not None
        assert response.data.draft.message.text == text
        assert response.data.draft.channel_cid == (
            f"{channel.channel_type}:{channel.channel_id}"
        )

    def test_delete_draft(self, channel: Channel, random_user):
        """Create a draft, delete it, and verify get raises an error."""
        text = f"draft-to-delete-{uuid.uuid4()}"
        channel.update(add_members=[ChannelMemberRequest(user_id=random_user.id)])

        _create_draft(channel, text, random_user.id)

        # verify draft exists
        response = channel.get_draft(user_id=random_user.id)
        assert response.data.draft is not None

        # delete draft
        channel.delete_draft(user_id=random_user.id)

        # verify draft is gone
        with pytest.raises(StreamAPIException):
            channel.get_draft(user_id=random_user.id)

    def test_thread_draft(self, channel: Channel, random_user):
        """Create a draft on a thread (with parent_id), get and delete it."""
        channel.update(add_members=[ChannelMemberRequest(user_id=random_user.id)])

        # send a parent message
        parent = channel.send_message(
            message=MessageRequest(text="thread parent", user_id=random_user.id)
        )
        parent_id = parent.data.message.id

        # create draft with parent_id
        text = f"thread-draft-{uuid.uuid4()}"
        _create_draft(channel, text, random_user.id, parent_id=parent_id)

        # get draft with parent_id
        response = channel.get_draft(user_id=random_user.id, parent_id=parent_id)
        assert response.data.draft is not None
        assert response.data.draft.message.text == text
        assert response.data.draft.message.parent_id == parent_id

        # delete draft with parent_id
        channel.delete_draft(user_id=random_user.id, parent_id=parent_id)

        with pytest.raises(StreamAPIException):
            channel.get_draft(user_id=random_user.id, parent_id=parent_id)

    def test_query_drafts(self, client: Stream, random_users):
        """Create drafts in 2 channels, query with various filters."""
        user_id = random_users[0].id

        # create 2 channels with the user as member
        channel_ids = [str(uuid.uuid4()), str(uuid.uuid4())]
        channels = []
        for cid in channel_ids:
            ch = client.chat.channel("messaging", cid)
            ch.get_or_create(
                data=ChannelInput(
                    created_by_id=user_id,
                    members=[ChannelMemberRequest(user_id=user_id)],
                )
            )
            channels.append(ch)

        # create a draft in each channel
        for i, ch in enumerate(channels):
            _create_draft(ch, f"draft-{i}-{uuid.uuid4()}", user_id)

        # query all drafts for user — should return at least 2
        response = client.chat.query_drafts(user_id=user_id)
        assert response.data.drafts is not None
        assert len(response.data.drafts) >= 2

        # query with channel_cid filter — should return 1
        target_cid = f"messaging:{channel_ids[0]}"
        response = client.chat.query_drafts(
            user_id=user_id,
            filter={"channel_cid": {"$eq": target_cid}},
        )
        assert len(response.data.drafts) == 1
        assert response.data.drafts[0].channel_cid == target_cid

        # query with sort by created_at descending
        response = client.chat.query_drafts(
            user_id=user_id,
            sort=[SortParamRequest(field="created_at", direction=-1)],
        )
        assert len(response.data.drafts) >= 2
        # verify descending order
        for j in range(len(response.data.drafts) - 1):
            assert (
                response.data.drafts[j].created_at
                >= response.data.drafts[j + 1].created_at
            )

        # query with limit=1 pagination
        response = client.chat.query_drafts(user_id=user_id, limit=1)
        assert len(response.data.drafts) == 1

        # cleanup
        try:
            client.chat.delete_channels(
                cids=[f"messaging:{cid}" for cid in channel_ids], hard_delete=True
            )
        except StreamAPIException:
            pass
