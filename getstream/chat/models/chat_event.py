# THIS FILE IS GENERATED FROM github.com/GetStream/protocol/tree/main/openapi-gen/templates/python/type.tmpl
from dataclasses import dataclass
from typing import Union
from json import loads

from getstream.chat.models.any_event import AnyEvent
from getstream.chat.models.channel_created_event import ChannelCreatedEvent
from getstream.chat.models.channel_deleted_event import ChannelDeletedEvent
from getstream.chat.models.channel_frozen_event import ChannelFrozenEvent
from getstream.chat.models.channel_hidden_event import ChannelHiddenEvent
from getstream.chat.models.channel_kicked_event import ChannelKickedEvent
from getstream.chat.models.channel_muted_event import ChannelMutedEvent
from getstream.chat.models.channel_truncated_event import ChannelTruncatedEvent
from getstream.chat.models.channel_un_frozen_event import ChannelUnFrozenEvent
from getstream.chat.models.channel_unmuted_event import ChannelUnmutedEvent
from getstream.chat.models.channel_updated_event import ChannelUpdatedEvent
from getstream.chat.models.channel_visible_event import ChannelVisibleEvent
from getstream.chat.models.health_check_event import HealthCheckEvent
from getstream.chat.models.member_added_event import MemberAddedEvent
from getstream.chat.models.member_removed_event import MemberRemovedEvent
from getstream.chat.models.member_updated_event import MemberUpdatedEvent
from getstream.chat.models.message_deleted_event import MessageDeletedEvent
from getstream.chat.models.message_flagged_event import MessageFlaggedEvent
from getstream.chat.models.message_new_event import MessageNewEvent
from getstream.chat.models.message_read_event import MessageReadEvent
from getstream.chat.models.message_unblocked_event import MessageUnblockedEvent
from getstream.chat.models.message_updated_event import MessageUpdatedEvent
from getstream.chat.models.notification_added_to_channel_event import (
    NotificationAddedToChannelEvent,
)
from getstream.chat.models.notification_channel_deleted_event import (
    NotificationChannelDeletedEvent,
)
from getstream.chat.models.notification_channel_mutes_updated_event import (
    NotificationChannelMutesUpdatedEvent,
)
from getstream.chat.models.notification_channel_truncated_event import (
    NotificationChannelTruncatedEvent,
)
from getstream.chat.models.notification_invite_accepted_event import (
    NotificationInviteAcceptedEvent,
)
from getstream.chat.models.notification_invite_rejected_event import (
    NotificationInviteRejectedEvent,
)
from getstream.chat.models.notification_invited_event import NotificationInvitedEvent
from getstream.chat.models.notification_mark_read_event import NotificationMarkReadEvent
from getstream.chat.models.notification_mark_unread_event import (
    NotificationMarkUnreadEvent,
)
from getstream.chat.models.notification_mutes_updated_event import (
    NotificationMutesUpdatedEvent,
)
from getstream.chat.models.notification_new_message_event import (
    NotificationNewMessageEvent,
)
from getstream.chat.models.notification_removed_from_channel_event import (
    NotificationRemovedFromChannelEvent,
)
from getstream.chat.models.reaction_deleted_event import ReactionDeletedEvent
from getstream.chat.models.reaction_new_event import ReactionNewEvent
from getstream.chat.models.reaction_updated_event import ReactionUpdatedEvent
from getstream.chat.models.typing_start_event import TypingStartEvent
from getstream.chat.models.typing_stop_event import TypingStopEvent
from getstream.chat.models.user_banned_event import UserBannedEvent
from getstream.chat.models.user_deactivated_event import UserDeactivatedEvent
from getstream.chat.models.user_deleted_event import UserDeletedEvent
from getstream.chat.models.user_flagged_event import UserFlaggedEvent
from getstream.chat.models.user_muted_event import UserMutedEvent
from getstream.chat.models.user_presence_changed_event import UserPresenceChangedEvent
from getstream.chat.models.user_reactivated_event import UserReactivatedEvent
from getstream.chat.models.user_unbanned_event import UserUnbannedEvent
from getstream.chat.models.user_unmuted_event import UserUnmutedEvent
from getstream.chat.models.user_unread_reminder_event import UserUnreadReminderEvent
from getstream.chat.models.user_updated_event import UserUpdatedEvent
from getstream.chat.models.user_watching_start_event import UserWatchingStartEvent
from getstream.chat.models.user_watching_stop_event import UserWatchingStopEvent

mapping = {
    "any": AnyEvent,
    "channel.created": ChannelCreatedEvent,
    "channel.deleted": ChannelDeletedEvent,
    "channel.frozen": ChannelFrozenEvent,
    "channel.hidden": ChannelHiddenEvent,
    "channel.kicked": ChannelKickedEvent,
    "channel.muted": ChannelMutedEvent,
    "channel.truncated": ChannelTruncatedEvent,
    "channel.unfrozen": ChannelUnFrozenEvent,
    "channel.unmuted": ChannelUnmutedEvent,
    "channel.updated": ChannelUpdatedEvent,
    "channel.visible": ChannelVisibleEvent,
    "custom": AnyEvent,
    "health.check": HealthCheckEvent,
    "member.added": MemberAddedEvent,
    "member.removed": MemberRemovedEvent,
    "member.updated": MemberUpdatedEvent,
    "message.deleted": MessageDeletedEvent,
    "message.flagged": MessageFlaggedEvent,
    "message.new": MessageNewEvent,
    "message.read": MessageReadEvent,
    "message.unblocked": MessageUnblockedEvent,
    "message.updated": MessageUpdatedEvent,
    "notification.added_to_channel": NotificationAddedToChannelEvent,
    "notification.channel_deleted": NotificationChannelDeletedEvent,
    "notification.channel_mutes_updated": NotificationChannelMutesUpdatedEvent,
    "notification.channel_truncated": NotificationChannelTruncatedEvent,
    "notification.invite_accepted": NotificationInviteAcceptedEvent,
    "notification.invite_rejected": NotificationInviteRejectedEvent,
    "notification.invited": NotificationInvitedEvent,
    "notification.mark_read": NotificationMarkReadEvent,
    "notification.mark_unread": NotificationMarkUnreadEvent,
    "notification.message_new": NotificationNewMessageEvent,
    "notification.mutes_updated": NotificationMutesUpdatedEvent,
    "notification.removed_from_channel": NotificationRemovedFromChannelEvent,
    "reaction.deleted": ReactionDeletedEvent,
    "reaction.new": ReactionNewEvent,
    "reaction.updated": ReactionUpdatedEvent,
    "typing.start": TypingStartEvent,
    "typing.stop": TypingStopEvent,
    "user.banned": UserBannedEvent,
    "user.deactivated": UserDeactivatedEvent,
    "user.deleted": UserDeletedEvent,
    "user.flagged": UserFlaggedEvent,
    "user.muted": UserMutedEvent,
    "user.presence.changed": UserPresenceChangedEvent,
    "user.reactivated": UserReactivatedEvent,
    "user.unbanned": UserUnbannedEvent,
    "user.unmuted": UserUnmutedEvent,
    "user.unread_message_reminder": UserUnreadReminderEvent,
    "user.updated": UserUpdatedEvent,
    "user.watching.start": UserWatchingStartEvent,
    "user.watching.stop": UserWatchingStopEvent,
}


@dataclass
class ChatEvent:
    event: Union[
        AnyEvent,
        AnyEvent,
        ChannelCreatedEvent,
        ChannelDeletedEvent,
        ChannelFrozenEvent,
        ChannelHiddenEvent,
        ChannelKickedEvent,
        ChannelMutedEvent,
        ChannelTruncatedEvent,
        ChannelUnFrozenEvent,
        ChannelUnmutedEvent,
        ChannelUpdatedEvent,
        ChannelVisibleEvent,
        HealthCheckEvent,
        MemberAddedEvent,
        MemberRemovedEvent,
        MemberUpdatedEvent,
        MessageDeletedEvent,
        MessageFlaggedEvent,
        MessageNewEvent,
        MessageReadEvent,
        MessageUnblockedEvent,
        MessageUpdatedEvent,
        NotificationAddedToChannelEvent,
        NotificationChannelDeletedEvent,
        NotificationChannelMutesUpdatedEvent,
        NotificationChannelTruncatedEvent,
        NotificationInviteAcceptedEvent,
        NotificationInviteRejectedEvent,
        NotificationInvitedEvent,
        NotificationMarkReadEvent,
        NotificationMarkUnreadEvent,
        NotificationMutesUpdatedEvent,
        NotificationNewMessageEvent,
        NotificationRemovedFromChannelEvent,
        ReactionDeletedEvent,
        ReactionNewEvent,
        ReactionUpdatedEvent,
        TypingStartEvent,
        TypingStopEvent,
        UserBannedEvent,
        UserDeactivatedEvent,
        UserDeletedEvent,
        UserFlaggedEvent,
        UserMutedEvent,
        UserPresenceChangedEvent,
        UserReactivatedEvent,
        UserUnbannedEvent,
        UserUnmutedEvent,
        UserUnreadReminderEvent,
        UserUpdatedEvent,
        UserWatchingStartEvent,
        UserWatchingStopEvent,
    ]

    @classmethod
    def from_json(j) -> "ChatEvent":
        dict_type = loads(j)["type"]
        return ChatEvent(event=mapping[dict_type].from_json(j))
