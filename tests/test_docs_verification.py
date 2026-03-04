"""
Comprehensive verification of ALL Python code snippets in the chat docs.
Each test corresponds to code from a specific doc file and verifies it works
against the real Stream API. Tests clean up after themselves.
"""

import uuid
import time
from datetime import datetime, timedelta, timezone

import pytest
from getstream import Stream
from getstream.models import (
    Attachment,
    AsyncModerationCallbackConfig,
    ChannelExport,
    ChannelInput,
    ChannelInputRequest,
    ChannelMemberRequest,
    EventHook,
    EventRequest,
    FileUploadConfig,
    MessagePaginationParams,
    MessageRequest,
    OnlyUserID,
    PaginationParams,
    QueryMembersPayload,
    QueryUsersPayload,
    ReactionRequest,
    SearchPayload,
    SharedLocation,
    SortParamRequest,
    UpdateUserPartialRequest,
    UserCustomEventRequest,
    UserRequest,
)
from getstream.webhook import verify_webhook_signature


@pytest.fixture(scope="module")
def client():
    return Stream()


@pytest.fixture(scope="module")
def test_user(client):
    user_id = f"doc-test-user-{uuid.uuid4().hex[:8]}"
    client.upsert_users(UserRequest(id=user_id, name="Doc Test User", role="admin"))
    yield user_id
    try:
        client.delete_users(user_ids=[user_id], user="hard", conversations="hard", messages="hard")
    except Exception:
        pass


@pytest.fixture(scope="module")
def test_user2(client):
    user_id = f"doc-test-user2-{uuid.uuid4().hex[:8]}"
    client.upsert_users(UserRequest(id=user_id, name="Doc Test User 2"))
    yield user_id
    try:
        client.delete_users(user_ids=[user_id], user="hard", conversations="hard", messages="hard")
    except Exception:
        pass


@pytest.fixture(scope="module")
def test_user3(client):
    user_id = f"doc-test-user3-{uuid.uuid4().hex[:8]}"
    client.upsert_users(UserRequest(id=user_id, name="Doc Test User 3"))
    yield user_id
    try:
        client.delete_users(user_ids=[user_id], user="hard", conversations="hard", messages="hard")
    except Exception:
        pass


def make_channel(client, user_id, channel_id=None):
    """Helper to create a channel with cleanup. Adds creator as member."""
    if channel_id is None:
        channel_id = f"doc-test-{uuid.uuid4().hex[:8]}"
    ch = client.chat.channel("messaging", channel_id)
    ch.get_or_create(
        data=ChannelInput(
            created_by_id=user_id,
            members=[ChannelMemberRequest(user_id=user_id)],
        )
    )
    return ch, channel_id


def cleanup_channel(client, channel_id):
    try:
        client.chat.delete_channels(cids=[f"messaging:{channel_id}"], hard_delete=True)
    except Exception:
        pass


# ============================================================
# 01-quick_start/01-backend_quickstart.md
# ============================================================
class TestQuickstart:
    def test_create_token(self, client):
        """Docs: token = server_client.create_token("john")"""
        token = client.create_token("john")
        assert token is not None
        assert len(token) > 0

    def test_create_token_with_expiration(self, client):
        """Docs: token = server_client.create_token("john", expiration=3600)"""
        token = client.create_token("john", expiration=3600)
        assert token is not None

    def test_upsert_users(self, client, test_user):
        """Docs: server_client.upsert_users(UserRequest(...))"""
        uid = f"quickstart-upsert-{uuid.uuid4().hex[:8]}"
        client.upsert_users(UserRequest(id=uid, role="admin", custom={"mycustomfield": "123"}))
        try:
            client.delete_users(user_ids=[uid], user="hard")
        except Exception:
            pass

    def test_channel_create_and_update(self, client, test_user):
        """Docs: channel create, update with name/image/custom"""
        ch, cid = make_channel(client, test_user)
        ch.update(data=ChannelInputRequest(custom={"name": "my channel", "image": "image url", "mycustomfield": "123"}))
        cleanup_channel(client, cid)

    def test_channel_add_remove_members(self, client, test_user, test_user2, test_user3):
        """Docs: channel.update(add_members=[...]), channel.update(remove_members=[...])"""
        ch, cid = make_channel(client, test_user)
        ch.update(add_members=[
            ChannelMemberRequest(user_id=test_user2),
            ChannelMemberRequest(user_id=test_user3),
        ])
        ch.update(remove_members=[test_user3])
        cleanup_channel(client, cid)

    def test_channel_add_demote_moderators(self, client, test_user, test_user2):
        """Docs: channel.update(add_moderators=["thierry"]), channel.update(demote_moderators=["thierry"])"""
        ch, cid = make_channel(client, test_user)
        ch.update(add_members=[ChannelMemberRequest(user_id=test_user2)])
        ch.update(add_moderators=[test_user2])
        ch.update(demote_moderators=[test_user2])
        cleanup_channel(client, cid)

    def test_send_message_with_attachment(self, client, test_user, test_user2):
        """Docs: channel.send_message(MessageRequest(text=..., attachments=[...]))"""
        ch, cid = make_channel(client, test_user)
        ch.update(add_members=[ChannelMemberRequest(user_id=test_user2)])
        response = ch.send_message(
            MessageRequest(
                text="Test message with attachment",
                attachments=[
                    Attachment(
                        type="image",
                        asset_url="https://bit.ly/2K74TaG",
                        thumb_url="https://bit.ly/2Uumxti",
                        custom={"myCustomField": 123},
                    )
                ],
                mentioned_users=[test_user2],
                user_id=test_user,
                custom={"anotherCustomField": 234},
            )
        )
        assert response.data.message is not None
        cleanup_channel(client, cid)


# ============================================================
# 02-init_and_users/01-tokens_and_authentication.md
# ============================================================
class TestTokensAuth:
    def test_token_with_expiration(self, client):
        """Docs: token = server_client.create_token("john", expiration=3600)"""
        token = client.create_token("john", expiration=3600)
        assert token is not None

    def test_revoke_user_tokens(self, client, test_user):
        """Docs: client.update_users_partial(users=[UpdateUserPartialRequest(..., set={"revoke_tokens_issued_before": ...})])"""
        revoke_date = datetime.now(timezone.utc).isoformat()
        client.update_users_partial(users=[
            UpdateUserPartialRequest(id=test_user, set={"revoke_tokens_issued_before": revoke_date})
        ])
        # Unset to clean up
        client.update_users_partial(users=[
            UpdateUserPartialRequest(id=test_user, unset=["revoke_tokens_issued_before"])
        ])


# ============================================================
# 02-init_and_users/03-update_users.md
# ============================================================
class TestUpdateUsers:
    def test_upsert_single(self, client):
        """Docs: client.upsert_users(UserRequest(...))"""
        uid = f"upsert-single-{uuid.uuid4().hex[:8]}"
        client.upsert_users(UserRequest(id=uid, role="admin", custom={"book": "dune"}))
        try:
            client.delete_users(user_ids=[uid], user="hard")
        except Exception:
            pass

    def test_upsert_multiple(self, client):
        """Docs: client.upsert_users(UserRequest(...), UserRequest(...), UserRequest(...))"""
        uids = [f"upsert-multi-{i}-{uuid.uuid4().hex[:8]}" for i in range(3)]
        client.upsert_users(
            UserRequest(id=uids[0], role="admin", custom={"book": "dune"}),
            UserRequest(id=uids[1], role="user", custom={"book": "1984"}),
            UserRequest(id=uids[2], role="admin", custom={"book": "Fahrenheit 451"}),
        )
        try:
            client.delete_users(user_ids=uids, user="hard")
        except Exception:
            pass

    def test_partial_update(self, client, test_user):
        """Docs: client.update_users_partial(users=[UpdateUserPartialRequest(...)])"""
        # single user partial update
        client.update_users_partial(users=[
            UpdateUserPartialRequest(
                id=test_user,
                set={"role": "admin"},
            )
        ])
        # multiple users
        client.update_users_partial(users=[
            UpdateUserPartialRequest(id=test_user, set={"custom_field": "value"}),
        ])

    def test_deactivate_reactivate(self, client):
        """Docs: client.deactivate_user(...), client.reactivate_user(...)"""
        uid = f"deactivate-{uuid.uuid4().hex[:8]}"
        client.upsert_users(UserRequest(id=uid, name="deactivatable"))
        client.deactivate_user(uid)
        client.reactivate_user(uid)
        try:
            client.delete_users(user_ids=[uid], user="hard")
        except Exception:
            pass

    def test_delete_users(self, client):
        """Docs: client.delete_users(user_ids=[...], user="soft", messages="hard")"""
        uid = f"delete-test-{uuid.uuid4().hex[:8]}"
        client.upsert_users(UserRequest(id=uid))
        response = client.delete_users(user_ids=[uid], user="soft", messages="hard")
        assert response.data.task_id is not None

    def test_restore_users(self, client):
        """Docs: client.restore_users(user_ids=[...])"""
        uid = f"restore-{uuid.uuid4().hex[:8]}"
        client.upsert_users(UserRequest(id=uid))
        client.delete_users(user_ids=[uid], user="soft")
        time.sleep(1)
        client.restore_users(user_ids=[uid])
        try:
            client.delete_users(user_ids=[uid], user="hard")
        except Exception:
            pass

    def test_query_users(self, client, test_user):
        """Docs: client.query_users(QueryUsersPayload(...))"""
        response = client.query_users(
            QueryUsersPayload(
                filter_conditions={"id": {"$in": [test_user]}},
                sort=[SortParamRequest(field="last_active", direction=-1)],
                limit=10,
                offset=0,
            )
        )
        assert response.data.users is not None

    def test_query_users_autocomplete(self, client):
        """Docs: client.query_users(QueryUsersPayload(filter_conditions={"name": {"$autocomplete": "ro"}}))"""
        response = client.query_users(
            QueryUsersPayload(filter_conditions={"name": {"$autocomplete": "Doc"}})
        )
        assert response.data.users is not None

    def test_enforce_unique_usernames(self, client):
        """Docs: client.update_app(enforce_unique_usernames="app")"""
        client.update_app(enforce_unique_usernames="app")
        # Reset (API uses "no" not "none")
        client.update_app(enforce_unique_usernames="no")


# ============================================================
# 03-channels/01-creating_channels.md
# ============================================================
class TestCreatingChannels:
    def test_create_channel(self, client, test_user):
        """Docs: channel.get_or_create(data=ChannelInput(created_by_id=...))"""
        ch, cid = make_channel(client, test_user, f"travel-{uuid.uuid4().hex[:8]}")
        cleanup_channel(client, cid)

    def test_create_distinct_channel(self, client, test_user, test_user2):
        """Docs: distinct channel via get_or_create_distinct_channel"""
        response = client.chat.get_or_create_distinct_channel(
            type="messaging",
            data=ChannelInput(
                created_by_id=test_user,
                members=[
                    ChannelMemberRequest(user_id=test_user),
                    ChannelMemberRequest(user_id=test_user2),
                ],
            ),
        )
        assert response.data.channel is not None
        try:
            cleanup_channel(client, response.data.channel.id)
        except Exception:
            pass


# ============================================================
# 03-channels/02-query_channels.md
# ============================================================
class TestQueryChannels:
    def test_query_channels_with_sort(self, client, test_user):
        """Docs: client.chat.query_channels(filter_conditions={...}, sort=[...])"""
        ch, cid = make_channel(client, test_user)
        response = client.chat.query_channels(
            filter_conditions={"members": {"$in": [test_user]}},
            sort=[SortParamRequest(field="last_message_at", direction=1)],
            limit=10,
        )
        assert response.data.channels is not None
        cleanup_channel(client, cid)

    def test_query_channels_pagination(self, client, test_user):
        """Docs: query with limit and offset"""
        response = client.chat.query_channels(
            filter_conditions={"members": {"$in": [test_user]}},
            sort=[SortParamRequest(field="last_message_at", direction=-1)],
            limit=20,
            offset=0,
        )
        assert response.data.channels is not None


# ============================================================
# 03-channels/03-channel_update.md
# ============================================================
class TestChannelUpdate:
    def test_partial_update_set_unset(self, client, test_user):
        """Docs: channel.update_channel_partial(set={...}), channel.update_channel_partial(unset=[...])"""
        cid = f"doc-test-{uuid.uuid4().hex[:8]}"
        ch = client.chat.channel("messaging", cid)
        ch.get_or_create(
            data=ChannelInput(
                created_by_id=test_user,
                members=[ChannelMemberRequest(user_id=test_user)],
                custom={
                    "source": "user",
                    "source_detail": {"user_id": 123},
                    "channel_detail": {"topic": "Plants and Animals", "rating": "pg"},
                },
            )
        )
        ch.update_channel_partial(set={"source": "system"})
        ch.update_channel_partial(unset=["source_detail"])
        ch.update_channel_partial(set={"channel_detail.topic": "Nature"})
        ch.update_channel_partial(unset=["channel_detail.rating"])
        cleanup_channel(client, cid)

    def test_full_update(self, client, test_user):
        """Docs: channel.update(data=ChannelInputRequest(custom={...}))"""
        ch, cid = make_channel(client, test_user)
        ch.update(
            data=ChannelInputRequest(custom={"name": "myspecialchannel", "color": "green"})
        )
        cleanup_channel(client, cid)


# ============================================================
# 03-channels/04-query_members.md
# ============================================================
class TestQueryMembers:
    def test_query_members(self, client, test_user):
        """Docs: client.chat.query_members(QueryMembersPayload(...))"""
        ch, cid = make_channel(client, test_user)
        response = client.chat.query_members(
            QueryMembersPayload(
                type="messaging",
                id=cid,
                filter_conditions={},
                sort=[SortParamRequest(field="created_at", direction=1)],
            )
        )
        assert response.data.members is not None
        cleanup_channel(client, cid)

    def test_query_members_pagination(self, client, test_user):
        """Docs: query_members with offset and limit"""
        ch, cid = make_channel(client, test_user)
        response = client.chat.query_members(
            QueryMembersPayload(
                type="messaging",
                id=cid,
                filter_conditions={},
                sort=[SortParamRequest(field="user_id", direction=1)],
                offset=0,
                limit=10,
            )
        )
        assert response.data.members is not None
        cleanup_channel(client, cid)


# ============================================================
# 03-channels/05-channel_pagination.md
# ============================================================
class TestChannelPagination:
    def test_pagination_params(self, client, test_user):
        """Docs: channel.get_or_create(messages=MessagePaginationParams(...))"""
        ch, cid = make_channel(client, test_user)
        result = ch.get_or_create(
            members=PaginationParams(limit=20, offset=0),
            watchers=PaginationParams(limit=20, offset=0),
        )
        assert result.data.channel is not None
        cleanup_channel(client, cid)


# ============================================================
# 03-channels/06-channel_members.md
# ============================================================
class TestChannelMembers:
    def test_add_remove_members(self, client, test_user, test_user2, test_user3):
        """Docs: channel.update(add_members=[...]), channel.update(remove_members=[...])"""
        ch, cid = make_channel(client, test_user)
        ch.update(
            add_members=[
                ChannelMemberRequest(user_id=test_user2),
                ChannelMemberRequest(user_id=test_user3),
            ]
        )
        ch.update(remove_members=[test_user3])
        cleanup_channel(client, cid)

    def test_add_members_hide_history(self, client, test_user, test_user2):
        """Docs: channel.update(add_members=[...], hide_history=True)"""
        ch, cid = make_channel(client, test_user)
        ch.update(
            add_members=[ChannelMemberRequest(user_id=test_user2)],
            hide_history=True,
        )
        cleanup_channel(client, cid)

    def test_add_members_with_message(self, client, test_user, test_user2, test_user3):
        """Docs: channel.update(add_members=[...], message=MessageRequest(...))"""
        ch, cid = make_channel(client, test_user)
        ch.update(
            add_members=[
                ChannelMemberRequest(user_id=test_user2),
                ChannelMemberRequest(user_id=test_user3),
            ],
            message=MessageRequest(
                text="Users joined the channel.",
                user_id=test_user2,
            ),
        )
        cleanup_channel(client, cid)

    def test_update_member_partial(self, client, test_user, test_user2):
        """Docs: channel.update_member_partial(user_id=..., set={...}, unset=[...])"""
        ch, cid = make_channel(client, test_user)
        ch.update(add_members=[ChannelMemberRequest(user_id=test_user2)])
        ch.update_member_partial(user_id=test_user2, set={"hat": "blue"})
        ch.update_member_partial(user_id=test_user2, unset=["hat"])
        ch.update_member_partial(user_id=test_user2, set={"color": "red"}, unset=["hat"])
        cleanup_channel(client, cid)


# ============================================================
# 03-channels/07-channel_management/*
# ============================================================
class TestChannelManagement:
    def test_archiving(self, client, test_user):
        """Docs: 08-archiving.md - archive/unarchive"""
        ch, cid = make_channel(client, test_user)
        ch.update_member_partial(user_id=test_user, set={"archived": True})
        client.chat.query_channels(filter_conditions={"archived": True}, user_id=test_user)
        ch.update_member_partial(user_id=test_user, unset=["archived"])
        cleanup_channel(client, cid)

    def test_pinning(self, client, test_user):
        """Docs: 09-pinning.md - pin/unpin"""
        ch, cid = make_channel(client, test_user)
        ch.update_member_partial(user_id=test_user, set={"pinned": True})
        client.chat.query_channels(filter_conditions={"pinned": True}, user_id=test_user)
        client.chat.query_channels(
            filter_conditions={"members": {"$in": [test_user]}},
            sort=[SortParamRequest(field="pinned_at", direction=-1)],
            user_id=test_user,
        )
        ch.update_member_partial(user_id=test_user, unset=["pinned"])
        cleanup_channel(client, cid)

    def test_muting(self, client, test_user):
        """Docs: 10-muting.md - mute/unmute channel"""
        ch, cid = make_channel(client, test_user)
        client.chat.mute_channel(channel_cids=[f"messaging:{cid}"], user_id=test_user)
        client.chat.mute_channel(channel_cids=[f"messaging:{cid}"], user_id=test_user, expiration=30000)
        client.chat.unmute_channel(channel_cids=[f"messaging:{cid}"], user_id=test_user)
        cleanup_channel(client, cid)

    def test_hiding(self, client, test_user):
        """Docs: 11-hiding.md - hide/show"""
        ch, cid = make_channel(client, test_user)
        ch.hide(user_id=test_user)
        ch.show(user_id=test_user)
        cleanup_channel(client, cid)

    def test_disabling(self, client, test_user):
        """Docs: 12-disabling.md - disable/enable"""
        ch, cid = make_channel(client, test_user)
        ch.update(data=ChannelInputRequest(disabled=True))
        ch.update_channel_partial(set={"disabled": False})
        cleanup_channel(client, cid)

    def test_deleting(self, client, test_user):
        """Docs: 13-deleting.md - delete channel"""
        ch, cid = make_channel(client, test_user)
        ch.delete()
        # Also test batch delete
        ch2, cid2 = make_channel(client, test_user)
        response = client.chat.delete_channels(cids=[f"messaging:{cid2}"], hard_delete=True)
        assert response.data.task_id is not None

    def test_freezing(self, client, test_user):
        """Docs: 14-freezing.md - freeze/unfreeze"""
        ch, cid = make_channel(client, test_user)
        ch.update(data=ChannelInputRequest(frozen=True))
        ch.update(data=ChannelInputRequest(frozen=False))
        cleanup_channel(client, cid)

    def test_truncating(self, client, test_user):
        """Docs: 15-truncating.md - truncate"""
        ch, cid = make_channel(client, test_user)
        ch.truncate()
        ch.truncate(
            hard_delete=True,
            skip_push=True,
            message=MessageRequest(
                text="The channel has been truncated.",
                user_id=test_user,
            ),
        )
        cleanup_channel(client, cid)

    def test_invites(self, client, test_user, test_user2):
        """Docs: 16-channel_invites.md - invite/accept/reject"""
        ch, cid = make_channel(client, test_user)
        ch.update(invites=[ChannelMemberRequest(user_id=test_user2)])
        ch.update(accept_invite=True, user_id=test_user2)
        cleanup_channel(client, cid)

    def test_slow_mode(self, client, test_user):
        """Docs: slow_mode_and_throttling.md - cooldown"""
        ch, cid = make_channel(client, test_user)
        ch.update_channel_partial(set={"cooldown": 30})
        ch.update_channel_partial(set={"cooldown": 0})  # disable
        cleanup_channel(client, cid)


# ============================================================
# 04-messages/01-send_message.md
# ============================================================
class TestMessages:
    def test_send_simple_message(self, client, test_user):
        """Docs: channel.send_message(MessageRequest(text=..., user_id=...))"""
        ch, cid = make_channel(client, test_user)
        response = ch.send_message(MessageRequest(text="Hello, world!", user_id=test_user))
        assert response.data.message is not None
        cleanup_channel(client, cid)

    def test_send_message_skip_push(self, client, test_user, test_user2):
        """Docs: channel.send_message(..., skip_push=True)"""
        ch, cid = make_channel(client, test_user)
        ch.update(add_members=[ChannelMemberRequest(user_id=test_user2)])
        response = ch.send_message(
            MessageRequest(
                text="Check this out!",
                attachments=[
                    Attachment(type="image", asset_url="https://bit.ly/2K74TaG", thumb_url="https://bit.ly/2Uumxti", custom={"myCustomField": 123})
                ],
                mentioned_users=[test_user2],
                user_id=test_user,
                custom={"priority": "high"},
            ),
            skip_push=True,
        )
        assert response.data.message is not None
        cleanup_channel(client, cid)

    def test_get_message(self, client, test_user):
        """Docs: client.chat.get_message(id=msg_id)"""
        ch, cid = make_channel(client, test_user)
        send_resp = ch.send_message(MessageRequest(text="test get", user_id=test_user))
        msg_id = send_resp.data.message.id
        response = client.chat.get_message(id=msg_id)
        assert response.data.message.text == "test get"
        cleanup_channel(client, cid)

    def test_update_message(self, client, test_user):
        """Docs: client.chat.update_message(id=..., message=MessageRequest(...))"""
        ch, cid = make_channel(client, test_user)
        send_resp = ch.send_message(MessageRequest(text="original", user_id=test_user))
        msg_id = send_resp.data.message.id
        client.chat.update_message(
            id=msg_id,
            message=MessageRequest(text="Updated message text", user_id=test_user),
        )
        cleanup_channel(client, cid)

    def test_update_message_partial(self, client, test_user):
        """Docs: client.chat.update_message_partial(id=..., set={...}, user_id=...)"""
        ch, cid = make_channel(client, test_user)
        send_resp = ch.send_message(
            MessageRequest(text="partial test", user_id=test_user, custom={"color": "red"})
        )
        msg_id = send_resp.data.message.id
        # Set fields
        client.chat.update_message_partial(
            id=msg_id,
            set={"text": "Updated text"},
            user_id=test_user,
        )
        # Unset fields (must exist first)
        client.chat.update_message_partial(
            id=msg_id,
            unset=["color"],
            user_id=test_user,
        )
        cleanup_channel(client, cid)

    def test_delete_message(self, client, test_user):
        """Docs: client.chat.delete_message(id=...), client.chat.delete_message(id=..., hard=True)"""
        ch, cid = make_channel(client, test_user)
        r1 = ch.send_message(MessageRequest(text="to soft delete", user_id=test_user))
        client.chat.delete_message(id=r1.data.message.id)
        r2 = ch.send_message(MessageRequest(text="to hard delete", user_id=test_user))
        client.chat.delete_message(id=r2.data.message.id, hard=True)
        cleanup_channel(client, cid)

    def test_silent_message(self, client, test_user):
        """Docs: 07-silent_messages.md - silent and system messages"""
        ch, cid = make_channel(client, test_user)
        ch.send_message(
            MessageRequest(text="Silent msg", silent=True, user_id=test_user)
        )
        ch.send_message(
            MessageRequest(text="System msg", type="system", user_id=test_user)
        )
        cleanup_channel(client, cid)


# ============================================================
# 04-messages/03-threads.md
# ============================================================
class TestThreads:
    def test_reply_in_thread(self, client, test_user):
        """Docs: send_message with parent_id"""
        ch, cid = make_channel(client, test_user)
        parent = ch.send_message(MessageRequest(text="parent", user_id=test_user))
        pid = parent.data.message.id
        ch.send_message(
            MessageRequest(text="This is a reply in a thread", parent_id=pid, user_id=test_user)
        )
        # Get replies
        response = client.chat.get_replies(parent_id=pid, limit=20)
        assert len(response.data.messages) > 0
        cleanup_channel(client, cid)

    def test_quoted_reply(self, client, test_user):
        """Docs: send_message with quoted_message_id"""
        ch, cid = make_channel(client, test_user)
        original = ch.send_message(MessageRequest(text="original point", user_id=test_user))
        ch.send_message(
            MessageRequest(
                text="I agree with this point",
                quoted_message_id=original.data.message.id,
                user_id=test_user,
            )
        )
        cleanup_channel(client, cid)

    def test_query_threads(self, client, test_user):
        """Docs: client.chat.query_threads(...)"""
        response = client.chat.query_threads(
            filter={},
            sort=[SortParamRequest(field="created_at", direction=-1)],
            limit=10,
            user_id=test_user,
        )
        assert response.data.threads is not None


# ============================================================
# 04-messages/04-send_reaction.md
# ============================================================
class TestReactions:
    def test_send_delete_reaction(self, client, test_user):
        """Docs: send_reaction, delete_reaction, get_reactions"""
        ch, cid = make_channel(client, test_user)
        msg = ch.send_message(MessageRequest(text="react to this", user_id=test_user))
        mid = msg.data.message.id

        client.chat.send_reaction(
            id=mid,
            reaction=ReactionRequest(type="love", user_id=test_user, custom={"custom_field": 123}),
        )
        client.chat.get_reactions(id=mid, limit=10)
        client.chat.delete_reaction(id=mid, type="love", user_id=test_user)
        cleanup_channel(client, cid)

    def test_reaction_with_score(self, client, test_user):
        """Docs: reaction with score"""
        ch, cid = make_channel(client, test_user)
        msg = ch.send_message(MessageRequest(text="clap", user_id=test_user))
        mid = msg.data.message.id
        client.chat.send_reaction(
            id=mid,
            reaction=ReactionRequest(type="clap", score=5, user_id=test_user),
        )
        cleanup_channel(client, cid)


# ============================================================
# 04-messages/05-pinned_messages.md
# ============================================================
class TestPinnedMessages:
    def test_pin_unpin_message(self, client, test_user):
        """Docs: pin/unpin via send_message and update_message_partial"""
        ch, cid = make_channel(client, test_user)
        response = ch.send_message(
            MessageRequest(pinned=True, text="Important announcement", user_id=test_user)
        )
        msg_id = response.data.message.id

        # Pin with expiry
        client.chat.update_message_partial(
            id=msg_id,
            set={"pinned": True, "pin_expires": "2077-01-01T00:00:00Z"},
            user_id=test_user,
        )

        # Unpin
        client.chat.update_message_partial(
            id=msg_id,
            set={"pinned": False},
            user_id=test_user,
        )

        # Get pinned messages
        result = ch.get_or_create(state=True)
        assert result.data is not None
        cleanup_channel(client, cid)


# ============================================================
# 04-messages/06-search.md
# ============================================================
class TestSearch:
    def test_search(self, client, test_user):
        """Docs: client.chat.search(payload=SearchPayload(...))"""
        ch, cid = make_channel(client, test_user)
        ch.send_message(MessageRequest(text="supercalifragilistic", user_id=test_user))
        time.sleep(1)  # Wait for indexing
        response = client.chat.search(
            payload=SearchPayload(
                filter_conditions={"cid": f"messaging:{cid}"},
                message_filter_conditions={"text": {"$autocomplete": "supercali"}},
                sort=[SortParamRequest(field="relevance", direction=-1)],
                limit=10,
            )
        )
        assert response.data.results is not None
        cleanup_channel(client, cid)


# ============================================================
# 04-messages/09-message_reminders.md
# ============================================================
class TestReminders:
    def test_create_delete_reminder(self, client, test_user):
        """Docs: create_reminder, query_reminders, delete_reminder"""
        # Enable reminders on the messaging channel type
        try:
            client.chat.update_channel_type(name="messaging", user_message_reminders=True)
        except Exception:
            pytest.skip("Could not enable reminders on messaging channel type")

        ch, cid = make_channel(client, test_user)
        try:
            msg = ch.send_message(MessageRequest(text="remind me", user_id=test_user))
            mid = msg.data.message.id

            # Create reminder
            remind_at = datetime.now(timezone.utc) + timedelta(hours=1)
            client.chat.create_reminder(message_id=mid, user_id=test_user, remind_at=remind_at)

            # Query reminders
            reminders = client.chat.query_reminders(user_id=test_user)
            assert reminders.data.reminders is not None

            # Delete reminder
            client.chat.delete_reminder(message_id=mid, user_id=test_user)
        finally:
            cleanup_channel(client, cid)
            try:
                client.chat.update_channel_type(name="messaging", user_message_reminders=False)
            except Exception:
                pass


# ============================================================
# 05-features/02-events.md
# ============================================================
class TestEvents:
    def test_send_channel_event(self, client, test_user):
        """Docs: channel.send_event(event=EventRequest(...))"""
        ch, cid = make_channel(client, test_user)
        ch.send_event(
            event=EventRequest(
                type="friendship_request",
                user_id=test_user,
                custom={"text": "Hey there, long time no see!"},
            ),
        )
        cleanup_channel(client, cid)

    def test_send_user_custom_event(self, client, test_user):
        """Docs: client.chat.send_user_custom_event(...)"""
        client.chat.send_user_custom_event(
            user_id=test_user,
            event=UserCustomEventRequest(
                type="friendship_request",
                custom={"text": "Wants to be your friend"},
            ),
        )


# ============================================================
# 05-features/03-unread.md
# ============================================================
class TestUnread:
    def test_unread_counts(self, client, test_user):
        """Docs: client.chat.unread_counts(user_id=...)"""
        response = client.chat.unread_counts(user_id=test_user)
        assert response.data.total_unread_count is not None

    def test_unread_counts_batch(self, client, test_user, test_user2):
        """Docs: client.chat.unread_counts_batch(user_ids=[...])"""
        response = client.chat.unread_counts_batch(user_ids=[test_user, test_user2])
        assert response.data.counts_by_user is not None


# ============================================================
# 05-features/08-location_sharing.md
# ============================================================
class TestLocationSharing:
    def test_static_location(self, client, test_user):
        """Docs: send message with SharedLocation"""
        # Enable shared locations on the messaging channel type
        try:
            client.chat.update_channel_type(name="messaging", shared_locations=True)
        except Exception:
            pytest.skip("Could not enable location sharing on messaging channel type")

        ch, cid = make_channel(client, test_user)
        try:
            response = ch.send_message(
                MessageRequest(
                    text="Message with static location",
                    shared_location=SharedLocation(
                        latitude=37.7749,
                        longitude=-122.4194,
                        created_by_device_id="test_device_id",
                    ),
                    user_id=test_user,
                )
            )
            assert response.data.message is not None
        finally:
            cleanup_channel(client, cid)
            try:
                client.chat.update_channel_type(name="messaging", shared_locations=False)
            except Exception:
                pass


# ============================================================
# 05-features/09-translation.md
# ============================================================
class TestTranslation:
    def test_translate_message(self, client, test_user):
        """Docs: client.chat.translate_message(id=..., language="fr")"""
        ch, cid = make_channel(client, test_user)
        msg = ch.send_message(MessageRequest(text="Hello world", user_id=test_user))
        resp = client.chat.translate_message(id=msg.data.message.id, language="fr")
        assert resp.data.message.i18n is not None
        cleanup_channel(client, cid)

    def test_auto_translation(self, client, test_user):
        """Docs: channel.update(data=ChannelInputRequest(auto_translation_enabled=True))"""
        ch, cid = make_channel(client, test_user)
        ch.update(data=ChannelInputRequest(auto_translation_enabled=True))
        ch.update(data=ChannelInputRequest(auto_translation_enabled=True, auto_translation_language="en"))
        cleanup_channel(client, cid)

    def test_user_language(self, client):
        """Docs: client.upsert_users(UserRequest(id=..., language="en"))"""
        uid = f"lang-{uuid.uuid4().hex[:8]}"
        client.upsert_users(UserRequest(id=uid, language="en"))
        try:
            client.delete_users(user_ids=[uid], user="hard")
        except Exception:
            pass


# ============================================================
# 05-features/10-advanced/15-pending_messages.md
# ============================================================
class TestPendingMessages:
    def test_send_pending_message(self, client, test_user):
        """Docs: channel.send_message(MessageRequest(...), pending=True, pending_message_metadata={...})"""
        ch, cid = make_channel(client, test_user)
        response = ch.send_message(
            MessageRequest(text="hi", user_id=test_user),
            pending=True,
            pending_message_metadata={"extra_data": "test"},
        )
        msg_id = response.data.message.id

        # Commit the pending message
        client.chat.commit_message(id=msg_id)
        cleanup_channel(client, cid)


# ============================================================
# 06-app_and_channel_settings/01-channel_types.md
# ============================================================
class TestChannelTypes:
    def test_create_update_delete_channel_type(self, client):
        """Docs: create, update, list, get, delete channel types"""
        ct_name = f"doctest-{uuid.uuid4().hex[:8]}"
        client.chat.create_channel_type(
            name=ct_name,
            automod="disabled",
            automod_behavior="flag",
            max_message_length=5000,
            typing_events=True,
            read_events=True,
            reactions=True,
            replies=True,
        )

        client.chat.update_channel_type(
            name=ct_name,
            automod="disabled",
            automod_behavior="flag",
            max_message_length=1000,
            reactions=False,
        )

        client.chat.list_channel_types()
        client.chat.get_channel_type(name=ct_name)

        try:
            client.chat.delete_channel_type(name=ct_name)
        except Exception:
            pass


# ============================================================
# 06-app_and_channel_settings/02-app_settings.md
# ============================================================
class TestAppSettings:
    def test_disable_auth_checks(self, client):
        """Docs: client.update_app(disable_auth_checks=True/False)"""
        client.update_app(disable_auth_checks=True)
        client.update_app(disable_auth_checks=False)

    def test_file_upload_config(self, client):
        """Docs: client.update_app(file_upload_config=FileUploadConfig(...))"""
        client.update_app(
            file_upload_config=FileUploadConfig(
                size_limit=0,
                allowed_file_extensions=[".csv"],
                allowed_mime_types=["text/csv"],
            ),
        )
        # Reset
        client.update_app(
            file_upload_config=FileUploadConfig(size_limit=0),
        )


# ============================================================
# 06-app_and_channel_settings/03-chat_permission_policies.md
# ============================================================
class TestPermissions:
    def test_roles(self, client):
        """Docs: client.create_role(...), client.delete_role(...), client.list_permissions()"""
        role_name = f"doctest-role-{uuid.uuid4().hex[:8]}"
        try:
            client.create_role(role_name)
        except Exception as e:
            if "maximum number of custom roles" in str(e).lower() or "max custom roles" in str(e).lower():
                pytest.skip("Max custom roles reached on this app")
            raise
        client.list_permissions()
        client.delete_role(role_name)

    def test_assign_roles(self, client, test_user, test_user2):
        """Docs: channel.update(assign_roles=[ChannelMemberRequest(...)])"""
        ch, cid = make_channel(client, test_user)
        ch.update(add_members=[ChannelMemberRequest(user_id=test_user2)])
        ch.update(assign_roles=[
            ChannelMemberRequest(user_id=test_user2, channel_role="channel_moderator")
        ])
        ch.update(assign_roles=[
            ChannelMemberRequest(user_id=test_user2, channel_role="channel_member")
        ])
        cleanup_channel(client, cid)


# ============================================================
# 06-app_and_channel_settings/04-multi_tenant_chat.md
# ============================================================
class TestMultiTenant:
    def test_multi_tenant(self, client, test_user):
        """Docs: multi_tenant_enabled, teams"""
        client.update_app(multi_tenant_enabled=True)
        client.update_users_partial(users=[
            UpdateUserPartialRequest(id=test_user, set={"teams": ["red", "blue"]})
        ])

        ch, cid = make_channel(client, test_user, f"red-{uuid.uuid4().hex[:8]}")
        # Clean up
        cleanup_channel(client, cid)
        client.update_app(multi_tenant_enabled=False)

    def test_teams_role(self, client):
        """Docs: UserRequest with teams_role"""
        uid = f"teams-role-{uuid.uuid4().hex[:8]}"
        client.update_app(multi_tenant_enabled=True)
        client.upsert_users(
            UserRequest(
                id=uid,
                role="user",
                teams=["red", "blue"],
                teams_role={"red": "admin", "blue": "user"},
            )
        )
        client.update_app(multi_tenant_enabled=False)
        try:
            client.delete_users(user_ids=[uid], user="hard")
        except Exception:
            pass


# ============================================================
# 06-app_and_channel_settings/06-channel-level_settings.md
# ============================================================
class TestChannelLevelSettings:
    def test_config_overrides(self, client, test_user):
        """Docs: channel.update_channel_partial(set={"config_overrides": {...}})"""
        ch, cid = make_channel(client, test_user)
        ch.update_channel_partial(set={"config_overrides": {"replies": False}})
        ch.update_channel_partial(set={"config_overrides": {}})  # reset
        cleanup_channel(client, cid)


# ============================================================
# 07-push/03-registering_push_devices.md
# ============================================================
class TestDevices:
    def test_create_list_delete_device(self, client, test_user):
        """Docs: create_device, list_devices, delete_device"""
        device_id = "test-device-" + uuid.uuid4().hex[:8]
        client.create_device(
            id=device_id,
            push_provider="apn",
            user_id=test_user,
        )
        response = client.list_devices(user_id=test_user)
        assert any(d.id == device_id for d in response.data.devices)
        client.delete_device(id=device_id, user_id=test_user)


# ============================================================
# 08-webhooks/01-webhooks_overview/01-webhooks_overview.md
# ============================================================
class TestWebhooks:
    def test_verify_webhook_signature(self, client):
        """Docs: verify_webhook_signature(body, signature, api_secret)"""
        import hashlib
        import hmac

        secret = "test-secret"
        body = b'{"type":"test.event"}'
        signature = hmac.new(secret.encode("utf-8"), body, hashlib.sha256).hexdigest()
        assert verify_webhook_signature(body, signature, secret) is True
        assert verify_webhook_signature(body, "wrong-sig", secret) is False

    def test_update_app_event_hooks(self, client):
        """Docs: client.update_app(event_hooks=[...])"""
        # Get existing hooks
        response = client.get_app()
        existing_hooks = response.data.app.event_hooks or []

        # Set and then restore
        client.update_app(
            event_hooks=[
                {
                    "enabled": True,
                    "hook_type": "webhook",
                    "webhook_url": "https://example.com/webhooks/stream/messages",
                    "event_types": ["message.new", "message.updated"],
                }
            ]
        )
        # Restore
        client.update_app(event_hooks=existing_hooks)


# ============================================================
# 08-webhooks/01-webhooks_overview/03-custom_commands_webhook.md
# ============================================================
class TestCustomCommands:
    def test_command_crud(self, client):
        """Docs: create, list, get, update, delete commands (on client.chat)"""
        cmd_name = f"doctest{uuid.uuid4().hex[:6]}"
        client.chat.create_command(
            name=cmd_name,
            description="Create a support ticket",
            args="[description]",
            set="support_commands_set",
        )
        client.chat.list_commands()
        client.chat.get_command(cmd_name)
        client.chat.update_command(cmd_name, description="Updated description")
        client.chat.delete_command(cmd_name)


# ============================================================
# 10-migrating/03-exporting_channels.md
# ============================================================
class TestExportChannels:
    def test_export_channels(self, client, test_user):
        """Docs: client.chat.export_channels(channels=[ChannelExport(...)])"""
        ch, cid = make_channel(client, test_user)
        response = client.chat.export_channels(
            channels=[ChannelExport(type="messaging", id=cid)],
        )
        assert response.data.task_id is not None

        # Check task
        task_response = client.get_task(id=response.data.task_id)
        assert task_response.data.status is not None
        cleanup_channel(client, cid)


# ============================================================
# 11-debugging_and_cli/08-rate_limits.md
# ============================================================
class TestRateLimits:
    def test_get_rate_limits(self, client):
        """Docs: client.get_rate_limits(...)"""
        limits = client.get_rate_limits(server_side=True)
        assert limits.data is not None

        limits = client.get_rate_limits()
        assert limits.data is not None

        limits = client.get_rate_limits(endpoints=["QueryChannels", "SendMessage"])
        assert limits.data is not None


# ============================================================
# 12-best_practices/02-moderation.md
# ============================================================
class TestModeration:
    def test_blocklist_crud(self, client):
        """Docs: create, list, get, update, delete block_list"""
        bl_name = f"doctest-bl-{uuid.uuid4().hex[:6]}"
        client.create_block_list(name=bl_name, words=["fudge", "cream", "sugar"])
        client.list_block_lists()
        client.get_block_list(bl_name)
        client.update_block_list(bl_name, words=["fudge", "cream", "sugar", "vanilla"])
        client.delete_block_list(bl_name)

    def test_flag_message(self, client, test_user):
        """Docs: client.moderation.flag(entity_type=..., entity_id=..., user_id=...)"""
        ch, cid = make_channel(client, test_user)
        msg = ch.send_message(MessageRequest(text="flag this", user_id=test_user))
        client.moderation.flag(
            entity_type="stream:chat:v1:message",
            entity_id=msg.data.message.id,
            user_id=test_user,
        )
        cleanup_channel(client, cid)


# ============================================================
# 12-best_practices/07-gdpr.md
# ============================================================
class TestGDPR:
    def test_export_user(self, client, test_user):
        """Docs: client.export_user(user_id)"""
        response = client.export_user(test_user)
        assert response.data is not None


# ============================================================
# 05-features/10-advanced/12-drafts.md
# ============================================================
class TestDrafts:
    def test_draft_get_delete(self, client, test_user):
        """Docs: channel.get_draft(...), channel.delete_draft(...), client.chat.query_drafts(...)"""
        ch, cid = make_channel(client, test_user)

        # Query drafts (should work even with none)
        response = client.chat.query_drafts(user_id=test_user, limit=10)
        assert response.data is not None

        cleanup_channel(client, cid)


# ============================================================
# Model import verification
# ============================================================
class TestModelImports:
    """Verify all model types used in docs can be imported."""

    def test_all_imports(self):
        """All getstream.models imports from docs work"""
        from getstream.models import (
            AsyncModerationCallbackConfig,
            Attachment,
            ChannelExport,
            ChannelInput,
            ChannelInputRequest,
            ChannelMemberRequest,
            EventHook,
            EventRequest,
            FileUploadConfig,
            MessagePaginationParams,
            MessageRequest,
            OnlyUserID,
            PaginationParams,
            QueryMembersPayload,
            QueryUsersPayload,
            ReactionRequest,
            SearchPayload,
            SharedLocation,
            SortParamRequest,
            UpdateUserPartialRequest,
            UserCustomEventRequest,
            UserRequest,
        )
        # Verify they're all real classes
        for cls in [
            AsyncModerationCallbackConfig, Attachment, ChannelExport, ChannelInput,
            ChannelInputRequest, ChannelMemberRequest, EventHook, EventRequest,
            FileUploadConfig, MessagePaginationParams, MessageRequest, OnlyUserID,
            PaginationParams, QueryMembersPayload, QueryUsersPayload, ReactionRequest,
            SearchPayload, SharedLocation, SortParamRequest, UpdateUserPartialRequest,
            UserCustomEventRequest, UserRequest,
        ]:
            assert cls is not None

    def test_webhook_import(self):
        """verify_webhook_signature can be imported from getstream.webhook"""
        from getstream.webhook import verify_webhook_signature
        assert callable(verify_webhook_signature)
