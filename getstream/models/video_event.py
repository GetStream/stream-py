# THIS FILE IS GENERATED FROM github.com/GetStream/protocol/tree/main/openapi-gen/templates/python/type.tmpl
from dataclasses import dataclass
from typing import Union
from json import loads

from getstream.models.blocked_user_event import BlockedUserEvent
from getstream.models.call_accepted_event import CallAcceptedEvent
from getstream.models.call_created_event import CallCreatedEvent
from getstream.models.call_ended_event import CallEndedEvent
from getstream.models.call_hls_broadcasting_failed_event import (
    CallHlsbroadcastingFailedEvent,
)
from getstream.models.call_hls_broadcasting_started_event import (
    CallHlsbroadcastingStartedEvent,
)
from getstream.models.call_hls_broadcasting_stopped_event import (
    CallHlsbroadcastingStoppedEvent,
)
from getstream.models.call_live_started_event import CallLiveStartedEvent
from getstream.models.call_member_added_event import CallMemberAddedEvent
from getstream.models.call_member_removed_event import CallMemberRemovedEvent
from getstream.models.call_member_updated_event import CallMemberUpdatedEvent
from getstream.models.call_member_updated_permission_event import (
    CallMemberUpdatedPermissionEvent,
)
from getstream.models.call_notification_event import CallNotificationEvent
from getstream.models.call_reaction_event import CallReactionEvent
from getstream.models.call_recording_failed_event import CallRecordingFailedEvent
from getstream.models.call_recording_ready_event import CallRecordingReadyEvent
from getstream.models.call_recording_started_event import CallRecordingStartedEvent
from getstream.models.call_recording_stopped_event import CallRecordingStoppedEvent
from getstream.models.call_rejected_event import CallRejectedEvent
from getstream.models.call_ring_event import CallRingEvent
from getstream.models.call_session_ended_event import CallSessionEndedEvent
from getstream.models.call_session_participant_joined_event import (
    CallSessionParticipantJoinedEvent,
)
from getstream.models.call_session_participant_left_event import (
    CallSessionParticipantLeftEvent,
)
from getstream.models.call_session_started_event import CallSessionStartedEvent
from getstream.models.call_updated_event import CallUpdatedEvent
from getstream.models.call_user_muted import CallUserMuted
from getstream.models.connected_event import ConnectedEvent
from getstream.models.connection_error_event import ConnectionErrorEvent
from getstream.models.custom_video_event import CustomVideoEvent
from getstream.models.health_check_event import HealthCheckEvent
from getstream.models.permission_request_event import PermissionRequestEvent
from getstream.models.unblocked_user_event import UnblockedUserEvent
from getstream.models.updated_call_permissions_event import UpdatedCallPermissionsEvent

mapping = {
    "call.accepted": CallAcceptedEvent,
    "call.blocked_user": BlockedUserEvent,
    "call.created": CallCreatedEvent,
    "call.ended": CallEndedEvent,
    "call.hls_broadcasting_failed": CallHlsbroadcastingFailedEvent,
    "call.hls_broadcasting_started": CallHlsbroadcastingStartedEvent,
    "call.hls_broadcasting_stopped": CallHlsbroadcastingStoppedEvent,
    "call.live_started": CallLiveStartedEvent,
    "call.member_added": CallMemberAddedEvent,
    "call.member_removed": CallMemberRemovedEvent,
    "call.member_updated": CallMemberUpdatedEvent,
    "call.member_updated_permission": CallMemberUpdatedPermissionEvent,
    "call.notification": CallNotificationEvent,
    "call.permission_request": PermissionRequestEvent,
    "call.permissions_updated": UpdatedCallPermissionsEvent,
    "call.reaction_new": CallReactionEvent,
    "call.recording_failed": CallRecordingFailedEvent,
    "call.recording_ready": CallRecordingReadyEvent,
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
    "call.user_muted": CallUserMuted,
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
        CallCreatedEvent,
        CallEndedEvent,
        CallHlsbroadcastingFailedEvent,
        CallHlsbroadcastingStartedEvent,
        CallHlsbroadcastingStoppedEvent,
        CallLiveStartedEvent,
        CallMemberAddedEvent,
        CallMemberRemovedEvent,
        CallMemberUpdatedEvent,
        CallMemberUpdatedPermissionEvent,
        CallNotificationEvent,
        CallReactionEvent,
        CallRecordingFailedEvent,
        CallRecordingReadyEvent,
        CallRecordingStartedEvent,
        CallRecordingStoppedEvent,
        CallRejectedEvent,
        CallRingEvent,
        CallSessionEndedEvent,
        CallSessionParticipantJoinedEvent,
        CallSessionParticipantLeftEvent,
        CallSessionStartedEvent,
        CallUpdatedEvent,
        CallUserMuted,
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
