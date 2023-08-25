from dataclasses import dataclass
from typing import Optional
from .model_blocked_user_event import BlockedUserEvent
from .model_unblocked_user_event import UnblockedUserEvent
from .model_call_accepted_event import CallAcceptedEvent
from .model_call_broadcasting_started_event import CallBroadcastingStartedEvent
from .model_call_broadcasting_stopped_event import CallBroadcastingStoppedEvent
from .model_call_created_event import CallCreatedEvent
from .model_call_ended_event import CallEndedEvent
from .model_call_live_started_event import CallLiveStartedEvent
from .model_call_member_added_event import CallMemberAddedEvent
from .model_call_member_removed_event import CallMemberRemovedEvent
from .model_call_member_updated_event import CallMemberUpdatedEvent
from .model_call_member_updated_permission_event import (
    CallMemberUpdatedPermissionEvent,
)
from .model_call_notification_event import CallNotificationEvent
from .model_call_reaction_event import CallReactionEvent
from .model_call_recording_started_event import CallRecordingStartedEvent
from .model_call_recording_stopped_event import CallRecordingStoppedEvent
from .model_call_rejected_event import CallRejectedEvent
from .model_call_ring_event import CallRingEvent
from .model_call_session_ended_event import CallSessionEndedEvent
from .model_call_session_participant_joined_event import (
    CallSessionParticipantJoinedEvent,
)
from .model_call_session_participant_left_event import (
    CallSessionParticipantLeftEvent,
)
from .model_call_session_started_event import CallSessionStartedEvent
from .model_call_updated_event import CallUpdatedEvent
from .model_connected_event import ConnectedEvent
from .model_connection_error_event import ConnectionErrorEvent
from .model_custom_video_event import CustomVideoEvent
from .model_health_check_event import HealthCheckEvent
from .model_permission_request_event import PermissionRequestEvent
from .model_updated_call_permissions_event import UpdatedCallPermissionsEvent


@dataclass
class VideoEvent:
    blocked_user_event: Optional[BlockedUserEvent] = None
    call_accepted_event: Optional[CallAcceptedEvent] = None
    call_broadcasting_started_event: Optional[CallBroadcastingStartedEvent] = None
    call_broadcasting_stopped_event: Optional[CallBroadcastingStoppedEvent] = None
    call_created_event: Optional[CallCreatedEvent] = None
    call_ended_event: Optional[CallEndedEvent] = None
    call_live_started_event: Optional[CallLiveStartedEvent] = None
    call_member_added_event: Optional[CallMemberAddedEvent] = None
    call_member_removed_event: Optional[CallMemberRemovedEvent] = None
    call_member_updated_event: Optional[CallMemberUpdatedEvent] = None
    call_member_updated_permission_event: Optional[
        CallMemberUpdatedPermissionEvent
    ] = None
    call_notification_event: Optional[CallNotificationEvent] = None
    call_reaction_event: Optional[CallReactionEvent] = None
    call_recording_started_event: Optional[CallRecordingStartedEvent] = None
    call_recording_stopped_event: Optional[CallRecordingStoppedEvent] = None
    call_rejected_event: Optional[CallRejectedEvent] = None
    call_ring_event: Optional[CallRingEvent] = None
    call_session_ended_event: Optional[CallSessionEndedEvent] = None
    call_session_participant_joined_event: Optional[
        CallSessionParticipantJoinedEvent
    ] = None
    call_session_participant_left_event: Optional[
        CallSessionParticipantLeftEvent
    ] = None
    call_session_started_event: Optional[CallSessionStartedEvent] = None
    call_updated_event: Optional[CallUpdatedEvent] = None
    connected_event: Optional[ConnectedEvent] = None
    connection_error_event: Optional[ConnectionErrorEvent] = None
    custom_video_event: Optional[CustomVideoEvent] = None
    health_check_event: Optional[HealthCheckEvent] = None
    permission_request_event: Optional[PermissionRequestEvent] = None
    unblocked_user_event: Optional[UnblockedUserEvent] = None
    updated_call_permissions_event: Optional[UpdatedCallPermissionsEvent] = None
