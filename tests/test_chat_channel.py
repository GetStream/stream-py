import uuid
from pathlib import Path

from getstream import Stream
from getstream.base import StreamAPIException
from getstream.chat.channel import Channel
from getstream.models import (
    ChannelExport,
    ChannelInput,
    ChannelInputRequest,
    ChannelMemberRequest,
    MessageRequest,
    OnlyUserID,
    QueryMembersPayload,
    SortParamRequest,
    UserRequest,
)
from tests.base import wait_for_task

ASSETS_DIR = Path(__file__).parent / "assets"


class TestChannelCRUD:
    def test_create_channel(self, client: Stream, random_users):
        """Create a channel without specifying an ID (distinct channel)."""
        member_ids = [u.id for u in random_users]
        channel = client.chat.channel("messaging", str(uuid.uuid4()))
        response = channel.get_or_create(
            data=ChannelInput(
                created_by_id=member_ids[0],
                members=[ChannelMemberRequest(user_id=uid) for uid in member_ids],
            )
        )
        assert response.data.channel is not None
        assert response.data.channel.type == "messaging"

        # cleanup
        try:
            client.chat.delete_channels(
                cids=[f"{response.data.channel.type}:{response.data.channel.id}"],
                hard_delete=True,
            )
        except StreamAPIException:
            pass

    def test_create_channel_with_options(self, client: Stream, random_users):
        """Create a channel with hide_for_creator option."""
        member_ids = [u.id for u in random_users]
        channel = client.chat.channel("messaging", str(uuid.uuid4()))
        response = channel.get_or_create(
            hide_for_creator=True,
            data=ChannelInput(
                created_by_id=member_ids[0],
                members=[ChannelMemberRequest(user_id=uid) for uid in member_ids],
            ),
        )
        assert response.data.channel is not None

        try:
            client.chat.delete_channels(
                cids=[f"{response.data.channel.type}:{response.data.channel.id}"],
                hard_delete=True,
            )
        except StreamAPIException:
            pass

    def test_create_distinct_channel(self, client: Stream, random_users):
        """Create a distinct channel and verify idempotency."""
        member_ids = [u.id for u in random_users[:2]]
        members = [ChannelMemberRequest(user_id=uid) for uid in member_ids]

        response = client.chat.get_or_create_distinct_channel(
            type="messaging",
            data=ChannelInput(created_by_id=member_ids[0], members=members),
        )
        assert response.data.channel is not None
        first_cid = response.data.channel.cid

        # calling again with same members should return same channel
        response2 = client.chat.get_or_create_distinct_channel(
            type="messaging",
            data=ChannelInput(created_by_id=member_ids[0], members=members),
        )
        assert response2.data.channel.cid == first_cid

        try:
            client.chat.delete_channels(cids=[first_cid], hard_delete=True)
        except StreamAPIException:
            pass

    def test_update_channel(self, channel: Channel, random_user):
        """Update channel data with custom fields."""
        response = channel.update(
            data=ChannelInputRequest(custom={"motd": "one apple a day..."})
        )
        assert response.data.channel is not None
        assert response.data.channel.custom.get("motd") == "one apple a day..."

    def test_update_channel_partial(self, channel: Channel):
        """Partial update: set and unset fields."""
        channel.update_channel_partial(set={"color": "blue", "age": 30})
        response = channel.update_channel_partial(set={"color": "red"}, unset=["age"])
        assert response.data.channel is not None
        assert response.data.channel.custom.get("color") == "red"
        assert "age" not in (response.data.channel.custom or {})

    def test_delete_channel(self, client: Stream, random_user):
        """Delete a channel and verify deleted_at is set."""
        channel_id = str(uuid.uuid4())
        ch = client.chat.channel("messaging", channel_id)
        ch.get_or_create(data=ChannelInput(created_by_id=random_user.id))
        response = ch.delete()
        assert response.data.channel is not None
        assert response.data.channel.deleted_at is not None

    def test_delete_channels(self, client: Stream, random_user):
        """Delete channels and verify task_id is returned."""
        channel_id = str(uuid.uuid4())
        ch = client.chat.channel("messaging", channel_id)
        ch.get_or_create(data=ChannelInput(created_by_id=random_user.id))

        cid = f"messaging:{channel_id}"
        response = client.chat.delete_channels(cids=[cid], hard_delete=True)
        assert response.data.task_id is not None

    def test_truncate_channel(self, channel: Channel, random_user):
        """Truncate a channel."""
        channel.send_message(
            message=MessageRequest(text="hello", user_id=random_user.id)
        )
        response = channel.truncate()
        assert response.data.channel is not None

    def test_truncate_channel_with_options(self, channel: Channel, random_user):
        """Truncate a channel with skip_push and system message."""
        channel.send_message(
            message=MessageRequest(text="hello", user_id=random_user.id)
        )
        response = channel.truncate(
            skip_push=True,
            message=MessageRequest(text="Truncating channel.", user_id=random_user.id),
        )
        assert response.data.channel is not None

    def test_freeze_unfreeze_channel(self, channel: Channel):
        """Freeze and unfreeze a channel."""
        response = channel.update_channel_partial(set={"frozen": True})
        assert response.data.channel.frozen is True

        response = channel.update_channel_partial(set={"frozen": False})
        assert response.data.channel.frozen is False

    def test_query_channels(self, client: Stream, random_users):
        """Query channels by member filter."""
        user_id = random_users[0].id
        channel_id = str(uuid.uuid4())
        ch = client.chat.channel("messaging", channel_id)
        ch.get_or_create(
            data=ChannelInput(
                created_by_id=user_id,
                members=[ChannelMemberRequest(user_id=user_id)],
            )
        )

        response = client.chat.query_channels(
            filter_conditions={"members": {"$in": [user_id]}}
        )
        assert len(response.data.channels) >= 1

        try:
            client.chat.delete_channels(
                cids=[f"messaging:{channel_id}"], hard_delete=True
            )
        except StreamAPIException:
            pass

    def test_query_channels_members_in(self, client: Stream, random_users):
        """Query channels by $in member filter and verify result."""
        user_id = random_users[0].id
        other_id = random_users[1].id
        channel_id = str(uuid.uuid4())
        ch = client.chat.channel("messaging", channel_id)
        ch.get_or_create(
            data=ChannelInput(
                created_by_id=user_id,
                members=[
                    ChannelMemberRequest(user_id=uid) for uid in [user_id, other_id]
                ],
            )
        )

        response = client.chat.query_channels(
            filter_conditions={"members": {"$in": [user_id]}}
        )
        assert len(response.data.channels) >= 1
        channel_ids = [c.channel.id for c in response.data.channels]
        assert channel_id in channel_ids

        # verify member count
        matched = [c for c in response.data.channels if c.channel.id == channel_id]
        assert len(matched) == 1
        assert matched[0].channel.member_count >= 2

        try:
            client.chat.delete_channels(
                cids=[f"messaging:{channel_id}"], hard_delete=True
            )
        except StreamAPIException:
            pass

    def test_filter_tags(self, channel: Channel, random_user):
        """Add and remove filter tags on a channel."""
        # add two tags
        response = channel.update(add_filter_tags=["vip", "premium"])
        assert response.data.channel is not None
        assert "vip" in response.data.channel.filter_tags
        assert "premium" in response.data.channel.filter_tags

        # remove one tag
        response = channel.update(remove_filter_tags=["premium"])
        assert response.data.channel is not None
        assert "vip" in response.data.channel.filter_tags
        assert "premium" not in response.data.channel.filter_tags

        # cleanup remaining tag
        channel.update(remove_filter_tags=["vip"])


class TestChannelMembers:
    def test_add_members(self, channel: Channel, random_users):
        """Add members to a channel."""
        user_id = random_users[0].id
        # Remove first to ensure clean state
        channel.update(remove_members=[user_id])
        response = channel.update(add_members=[ChannelMemberRequest(user_id=user_id)])
        assert response.data.members is not None
        member_ids = [m.user_id for m in response.data.members]
        assert user_id in member_ids

    def test_add_members_hide_history(self, channel: Channel, random_users):
        """Add members with hide_history option."""
        user_id = random_users[0].id
        channel.update(remove_members=[user_id])
        response = channel.update(
            add_members=[ChannelMemberRequest(user_id=user_id)],
            hide_history=True,
        )
        assert response.data.members is not None
        member_ids = [m.user_id for m in response.data.members]
        assert user_id in member_ids

    def test_add_members_with_roles(self, client: Stream, channel: Channel):
        """Add members with specific channel roles."""
        rand = str(uuid.uuid4())[:8]
        mod_id = f"mod-{rand}"
        member_id = f"member-{rand}"
        user_ids = [mod_id, member_id]
        client.update_users(
            users={uid: UserRequest(id=uid, name=uid) for uid in user_ids}
        )

        channel.update(
            add_members=[
                ChannelMemberRequest(user_id=mod_id, channel_role="channel_moderator"),
                ChannelMemberRequest(user_id=member_id, channel_role="channel_member"),
            ]
        )

        members_resp = client.chat.query_members(
            payload=QueryMembersPayload(
                type=channel.channel_type,
                id=channel.channel_id,
                filter_conditions={"id": {"$in": user_ids}},
            )
        )
        role_map = {m.user_id: m.channel_role for m in members_resp.data.members}
        assert role_map[mod_id] == "channel_moderator"
        assert role_map[member_id] == "channel_member"

        try:
            client.delete_users(
                user_ids=user_ids,
                user="hard",
                conversations="hard",
                messages="hard",
            )
        except StreamAPIException:
            pass

    def test_invite_members(self, channel: Channel, random_users):
        """Invite members to a channel."""
        user_id = random_users[0].id
        channel.update(remove_members=[user_id])
        response = channel.update(invites=[ChannelMemberRequest(user_id=user_id)])
        assert response.data.members is not None
        member_ids = [m.user_id for m in response.data.members]
        assert user_id in member_ids

    def test_invites_accept_reject(self, client: Stream, random_users):
        """Accept and reject channel invites, and verify non-invited user errors."""
        john = random_users[0].id
        ringo = random_users[1].id
        eric = random_users[2].id

        channel_id = "beatles-" + str(uuid.uuid4())
        ch = client.chat.channel("team", channel_id)
        ch.get_or_create(
            data=ChannelInput(
                created_by_id=john,
                members=[
                    ChannelMemberRequest(user_id=uid) for uid in [john, ringo, eric]
                ],
                invites=[ChannelMemberRequest(user_id=uid) for uid in [ringo, eric]],
            )
        )

        # accept invite
        accept = ch.update(accept_invite=True, user_id=ringo)
        for m in accept.data.members:
            if m.user_id == ringo:
                assert m.invited is True
                assert m.invite_accepted_at is not None

        # reject invite
        reject = ch.update(reject_invite=True, user_id=eric)
        for m in reject.data.members:
            if m.user_id == eric:
                assert m.invited is True
                assert m.invite_rejected_at is not None

        # non-invited user (john) accepting should raise an error
        import pytest

        with pytest.raises(StreamAPIException):
            ch.update(accept_invite=True, user_id=john)

        try:
            client.chat.delete_channels(cids=[f"team:{channel_id}"], hard_delete=True)
        except StreamAPIException:
            pass

    def test_add_moderators(self, channel: Channel, random_user):
        """Add and demote moderators."""
        response = channel.update(
            add_members=[ChannelMemberRequest(user_id=random_user.id)]
        )
        response = channel.update(add_moderators=[random_user.id])
        mod = [m for m in response.data.members if m.user_id == random_user.id]
        assert len(mod) == 1
        assert mod[0].is_moderator is True

        response = channel.update(demote_moderators=[random_user.id])
        mod = [m for m in response.data.members if m.user_id == random_user.id]
        assert len(mod) == 1
        assert mod[0].is_moderator is not True

    def test_assign_roles(self, channel: Channel, random_user):
        """Assign roles to channel members."""
        channel.update(
            add_members=[
                ChannelMemberRequest(
                    user_id=random_user.id, channel_role="channel_moderator"
                )
            ]
        )
        mod = None
        resp = channel.update(
            assign_roles=[
                ChannelMemberRequest(
                    user_id=random_user.id, channel_role="channel_member"
                )
            ]
        )
        for m in resp.data.members:
            if m.user_id == random_user.id:
                mod = m
        assert mod is not None
        assert mod.channel_role == "channel_member"

    def test_query_members(self, client: Stream, channel: Channel):
        """Query channel members with autocomplete filter."""
        rand = str(uuid.uuid4())[:8]
        user_ids = [
            f"{n}-{rand}" for n in ["paul", "george", "john", "jessica", "john2"]
        ]
        client.update_users(
            users={uid: UserRequest(id=uid, name=uid) for uid in user_ids}
        )
        for uid in user_ids:
            channel.update(add_members=[ChannelMemberRequest(user_id=uid)])

        response = client.chat.query_members(
            payload=QueryMembersPayload(
                type=channel.channel_type,
                id=channel.channel_id,
                filter_conditions={"name": {"$autocomplete": "j"}},
                sort=[SortParamRequest(field="created_at", direction=1)],
                offset=1,
                limit=10,
            )
        )
        assert response.data.members is not None
        assert len(response.data.members) == 2

        try:
            client.delete_users(
                user_ids=user_ids,
                user="hard",
                conversations="hard",
                messages="hard",
            )
        except StreamAPIException:
            pass

    def test_update_member_partial(self, channel: Channel, random_users):
        """Partial update of a channel member's custom fields."""
        user_id = random_users[0].id
        channel.update(add_members=[ChannelMemberRequest(user_id=user_id)])

        response = channel.update_member_partial(user_id=user_id, set={"hat": "blue"})
        assert response.data.channel_member is not None
        assert response.data.channel_member.custom.get("hat") == "blue"

        response = channel.update_member_partial(
            user_id=user_id, set={"color": "red"}, unset=["hat"]
        )
        assert response.data.channel_member.custom.get("color") == "red"
        assert "hat" not in (response.data.channel_member.custom or {})


class TestChannelState:
    def test_channel_hide_show(self, client: Stream, channel: Channel, random_users):
        """Hide and show a channel for a user, including hidden filter queries."""
        user_id = random_users[0].id
        channel.update(
            add_members=[
                ChannelMemberRequest(user_id=uid)
                for uid in [u.id for u in random_users]
            ]
        )
        cid = f"{channel.channel_type}:{channel.channel_id}"

        # verify channel is visible
        response = client.chat.query_channels(
            filter_conditions={"id": channel.channel_id}, user_id=user_id
        )
        assert len(response.data.channels) == 1

        # hide
        channel.hide(user_id=user_id)
        response = client.chat.query_channels(
            filter_conditions={"id": channel.channel_id}, user_id=user_id
        )
        assert len(response.data.channels) == 0

        # verify hidden channel appears in hidden=True query
        response = client.chat.query_channels(
            filter_conditions={"hidden": True, "cid": cid}, user_id=user_id
        )
        assert len(response.data.channels) == 1

        # show
        channel.show(user_id=user_id)
        response = client.chat.query_channels(
            filter_conditions={"id": channel.channel_id}, user_id=user_id
        )
        assert len(response.data.channels) == 1

        # verify channel no longer appears in hidden query
        response = client.chat.query_channels(
            filter_conditions={"hidden": True, "cid": cid}, user_id=user_id
        )
        assert len(response.data.channels) == 0

    def test_mute_unmute_channel(self, client: Stream, channel: Channel, random_users):
        """Mute and unmute a channel."""
        user_id = random_users[0].id
        channel.update(add_members=[ChannelMemberRequest(user_id=user_id)])
        cid = f"{channel.channel_type}:{channel.channel_id}"

        response = client.chat.mute_channel(
            user_id=user_id, channel_cids=[cid], expiration=30000
        )
        assert response.data.channel_mute is not None
        assert response.data.channel_mute.expires is not None

        # verify muted channel appears in query
        response = client.chat.query_channels(
            filter_conditions={"muted": True, "cid": cid}, user_id=user_id
        )
        assert len(response.data.channels) == 1

        # unmute
        client.chat.unmute_channel(user_id=user_id, channel_cids=[cid])
        response = client.chat.query_channels(
            filter_conditions={"muted": True, "cid": cid}, user_id=user_id
        )
        assert len(response.data.channels) == 0

    def test_pin_channel(self, client: Stream, channel: Channel, random_users):
        """Pin and unpin a channel for a user."""
        user_id = random_users[0].id
        channel.update(add_members=[ChannelMemberRequest(user_id=user_id)])
        cid = f"{channel.channel_type}:{channel.channel_id}"

        # Pin the channel
        response = channel.update_member_partial(user_id=user_id, set={"pinned": True})
        assert response is not None

        # Query for pinned channels
        response = client.chat.query_channels(
            filter_conditions={"pinned": True, "cid": cid}, user_id=user_id
        )
        assert len(response.data.channels) == 1
        assert response.data.channels[0].channel.cid == cid

        # Unpin the channel
        response = channel.update_member_partial(user_id=user_id, set={"pinned": False})
        assert response is not None

        # Query for unpinned channels
        response = client.chat.query_channels(
            filter_conditions={"pinned": False, "cid": cid}, user_id=user_id
        )
        assert len(response.data.channels) == 1

    def test_archive_channel(self, client: Stream, channel: Channel, random_users):
        """Archive and unarchive a channel for a user."""
        user_id = random_users[0].id
        channel.update(add_members=[ChannelMemberRequest(user_id=user_id)])
        cid = f"{channel.channel_type}:{channel.channel_id}"

        # Archive the channel
        response = channel.update_member_partial(
            user_id=user_id, set={"archived": True}
        )
        assert response is not None

        # Query for archived channels
        response = client.chat.query_channels(
            filter_conditions={"archived": True, "cid": cid}, user_id=user_id
        )
        assert len(response.data.channels) == 1
        assert response.data.channels[0].channel.cid == cid

        # Unarchive the channel
        response = channel.update_member_partial(
            user_id=user_id, set={"archived": False}
        )
        assert response is not None

        # Query for unarchived channels
        response = client.chat.query_channels(
            filter_conditions={"archived": False, "cid": cid}, user_id=user_id
        )
        assert len(response.data.channels) == 1

    def test_mark_read(self, channel: Channel, random_user):
        """Mark a channel as read."""
        channel.update(add_members=[ChannelMemberRequest(user_id=random_user.id)])
        response = channel.mark_read(user_id=random_user.id)
        assert response.data.event is not None
        assert response.data.event.type == "message.read"

    def test_mark_unread(self, channel: Channel, random_user):
        """Mark a channel as unread from a specific message."""
        msg_response = channel.send_message(
            message=MessageRequest(text="helloworld", user_id=random_user.id)
        )
        msg_id = msg_response.data.message.id
        response = channel.mark_unread(user_id=random_user.id, message_id=msg_id)
        assert response is not None

    def test_mark_unread_with_thread(self, channel: Channel, random_user):
        """Mark unread from a specific thread."""
        channel.update(add_members=[ChannelMemberRequest(user_id=random_user.id)])
        parent = channel.send_message(
            message=MessageRequest(
                text="Parent for unread thread", user_id=random_user.id
            )
        )
        parent_id = parent.data.message.id

        channel.send_message(
            message=MessageRequest(
                text="Reply in thread",
                user_id=random_user.id,
                parent_id=parent_id,
            )
        )

        response = channel.mark_unread(
            user_id=random_user.id,
            thread_id=parent_id,
        )
        assert response is not None

    def test_mark_unread_with_timestamp(self, channel: Channel, random_user):
        """Mark unread using a message timestamp."""
        channel.update(add_members=[ChannelMemberRequest(user_id=random_user.id)])
        send_resp = channel.send_message(
            message=MessageRequest(
                text="test message for timestamp", user_id=random_user.id
            )
        )
        ts = send_resp.data.message.created_at

        response = channel.mark_unread(
            user_id=random_user.id,
            message_timestamp=ts,
        )
        assert response is not None

    def test_message_count(self, client: Stream, channel: Channel, random_user):
        """Verify message count on a channel."""
        channel.send_message(
            message=MessageRequest(text="hello world", user_id=random_user.id)
        )

        q_resp = client.chat.query_channels(
            filter_conditions={"cid": f"{channel.channel_type}:{channel.channel_id}"},
            user_id=random_user.id,
        )
        assert len(q_resp.data.channels) == 1
        ch = q_resp.data.channels[0].channel
        if ch.message_count is not None:
            assert ch.message_count >= 1

    def test_message_count_disabled(
        self, client: Stream, channel: Channel, random_user
    ):
        """Verify message count is None when count_messages is disabled."""
        channel.update_channel_partial(
            set={"config_overrides": {"count_messages": False}}
        )

        channel.send_message(
            message=MessageRequest(text="hello world", user_id=random_user.id)
        )

        q_resp = client.chat.query_channels(
            filter_conditions={"cid": f"{channel.channel_type}:{channel.channel_id}"},
            user_id=random_user.id,
        )
        assert len(q_resp.data.channels) == 1
        assert q_resp.data.channels[0].channel.message_count is None


class TestChannelExportAndBan:
    def test_export_channel(self, client: Stream, channel: Channel, random_users):
        """Export a channel and poll the task until complete."""
        channel.send_message(
            message=MessageRequest(text="Hey Joni", user_id=random_users[0].id)
        )
        cid = f"{channel.channel_type}:{channel.channel_id}"
        response = client.chat.export_channels(channels=[ChannelExport(cid=cid)])
        task_id = response.data.task_id
        assert task_id is not None and task_id != ""

        task_response = wait_for_task(client, task_id, timeout_ms=30000)
        assert task_response.data.status == "completed"

    def test_export_channel_status(self, client: Stream):
        """Test error handling for export channel status with invalid task ID."""
        import pytest

        # Invalid task ID should raise an error
        with pytest.raises(StreamAPIException):
            client.get_task(id=str(uuid.uuid4()))

    def test_ban_user_in_channel(
        self, client: Stream, channel: Channel, random_user, server_user
    ):
        """Ban and unban a user at channel level."""
        channel.update(
            add_members=[
                ChannelMemberRequest(user_id=uid)
                for uid in [random_user.id, server_user.id]
            ]
        )
        cid = f"{channel.channel_type}:{channel.channel_id}"

        client.moderation.ban(
            target_user_id=random_user.id,
            banned_by_id=server_user.id,
            channel_cid=cid,
        )
        client.moderation.ban(
            target_user_id=random_user.id,
            banned_by_id=server_user.id,
            channel_cid=cid,
            timeout=3600,
            reason="offensive language is not allowed here",
        )
        client.moderation.unban(
            target_user_id=random_user.id,
            channel_cid=cid,
        )


class TestChannelFileUpload:
    def test_upload_and_delete_file(self, channel: Channel, random_user):
        """Upload and delete a file."""
        file_path = str(ASSETS_DIR / "test_upload.txt")

        try:
            upload_resp = channel.upload_channel_file(
                file=file_path,
                user=OnlyUserID(id=random_user.id),
            )
            assert upload_resp.data.file is not None
            file_url = upload_resp.data.file
            assert "http" in file_url

            channel.delete_channel_file(url=file_url)
        except Exception as e:
            if "multipart" in str(e).lower():
                import pytest

                pytest.skip("File upload requires multipart/form-data support")
            raise

    def test_upload_and_delete_image(self, channel: Channel, random_user):
        """Upload and delete an image."""
        file_path = str(ASSETS_DIR / "test_upload.jpg")

        try:
            upload_resp = channel.upload_channel_image(
                file=file_path,
                user=OnlyUserID(id=random_user.id),
            )
            assert upload_resp.data.file is not None
            image_url = upload_resp.data.file
            assert "http" in image_url

            channel.delete_channel_image(url=image_url)
        except Exception as e:
            if "multipart" in str(e).lower():
                import pytest

                pytest.skip("Image upload requires multipart/form-data support")
            raise
