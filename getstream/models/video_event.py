from dataclasses import dataclass

from typing import Union
from json import loads

from blocked_user_event import BlockedUserEvent
from call_accepted_event import CallAcceptedEvent
from call_broadcasting_started_event import CallBroadcastingStartedEvent
from call_broadcasting_stopped_event import CallBroadcastingStoppedEvent
from call_created_event import CallCreatedEvent
from call_ended_event import CallEndedEvent
from call_live_started_event import CallLiveStartedEvent
from call_member_added_event import CallMemberAddedEvent
from call_member_removed_event import CallMemberRemovedEvent
from call_member_updated_event import CallMemberUpdatedEvent
from call_member_updated_permission_event import CallMemberUpdatedPermissionEvent
from call_notification_event import CallNotificationEvent
from call_reaction_event import CallReactionEvent
from call_recording_started_event import CallRecordingStartedEvent
from call_recording_stopped_event import CallRecordingStoppedEvent
from call_rejected_event import CallRejectedEvent
from call_ring_event import CallRingEvent
from call_session_ended_event import CallSessionEndedEvent
from call_session_participant_joined_event import CallSessionParticipantJoinedEvent
from call_session_participant_left_event import CallSessionParticipantLeftEvent
from call_session_started_event import CallSessionStartedEvent
from call_updated_event import CallUpdatedEvent
from connected_event import ConnectedEvent
from connection_error_event import ConnectionErrorEvent
from custom_video_event import CustomVideoEvent
from health_check_event import HealthCheckEvent
from permission_request_event import PermissionRequestEvent
from unblocked_user_event import UnblockedUserEvent
from updated_call_permissions_event import UpdatedCallPermissionsEvent

mapping = {
    "call.accepted": CallAcceptedEvent,
    "call.blocked_user": BlockedUserEvent,
    "call.broadcasting_started": CallBroadcastingStartedEvent,
    "call.broadcasting_stopped": CallBroadcastingStoppedEvent,
    "call.created": CallCreatedEvent,
    "call.ended": CallEndedEvent,
    "call.live_started": CallLiveStartedEvent,
    "call.member_added": CallMemberAddedEvent,
    "call.member_removed": CallMemberRemovedEvent,
    "call.member_updated": CallMemberUpdatedEvent,
    "call.member_updated_permission": CallMemberUpdatedPermissionEvent,
    "call.notification": CallNotificationEvent,
    "call.permission_request": PermissionRequestEvent,
    "call.permissions_updated": UpdatedCallPermissionsEvent,
    "call.reaction_new": CallReactionEvent,
    "call.recording_started": CallRecordingStartedEvent,
    "call.recording_stopped": CallRecordingStoppedEvent,
    "call.rejected": CallRejectedEvent,
    "call.ring": CallRingEvent,
    "call.session_ended": CallSessionEndedEvent,
    "call.session_participant_joined": CallSessionParticipantJoinedEvent,
    "call.session_participant_left": CallSessionParticipantLeftEvent,
    "call.session_started": CallSessionStartedEvent,
    "call.unblocked_user": UnblockedUserEvent,
    "call.updated": CallUpdatedEvent,
    "connection.error": ConnectionErrorEvent,
    "connection.ok": ConnectedEvent,
    "custom": CustomVideoEvent,
    "health.check": HealthCheckEvent,
}


@dataclass
class VideoEvent:
    event: Union[
        BlockedUserEvent,
        CallAcceptedEvent,
        CallBroadcastingStartedEvent,
        CallBroadcastingStoppedEvent,
        CallCreatedEvent,
        CallEndedEvent,
        CallLiveStartedEvent,
        CallMemberAddedEvent,
        CallMemberRemovedEvent,
        CallMemberUpdatedEvent,
        CallMemberUpdatedPermissionEvent,
        CallNotificationEvent,
        CallReactionEvent,
        CallRecordingStartedEvent,
        CallRecordingStoppedEvent,
        CallRejectedEvent,
        CallRingEvent,
        CallSessionEndedEvent,
        CallSessionParticipantJoinedEvent,
        CallSessionParticipantLeftEvent,
        CallSessionStartedEvent,
        CallUpdatedEvent,
        ConnectedEvent,
        ConnectionErrorEvent,
        CustomVideoEvent,
        HealthCheckEvent,
        PermissionRequestEvent,
        UnblockedUserEvent,
        UpdatedCallPermissionsEvent,
    ]

    @classmethod
    def from_json(j) -> "VideoEvent":
        dict_type = loads(j)["type"]
        return VideoEvent(event=mapping[dict_type].from_json(j))
