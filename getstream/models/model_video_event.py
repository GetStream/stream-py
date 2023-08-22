from dataclasses import dataclass
from typing import Optional


@dataclass
class VideoEvent:
    BlockedUserEvent: Optional[BlockedUserEvent] = None
    CallAcceptedEvent: Optional[CallAcceptedEvent] = None
    CallBroadcastingStartedEvent: Optional[CallBroadcastingStartedEvent] = None
    CallBroadcastingStoppedEvent: Optional[CallBroadcastingStoppedEvent] = None
    CallCreatedEvent: Optional[CallCreatedEvent] = None
    CallEndedEvent: Optional[CallEndedEvent] = None
    CallLiveStartedEvent: Optional[CallLiveStartedEvent] = None
    CallMemberAddedEvent: Optional[CallMemberAddedEvent] = None
    CallMemberRemovedEvent: Optional[CallMemberRemovedEvent] = None
    CallMemberUpdatedEvent: Optional[CallMemberUpdatedEvent] = None
    CallMemberUpdatedPermissionEvent: Optional[CallMemberUpdatedPermissionEvent] = None
    CallNotificationEvent: Optional[CallNotificationEvent] = None
    CallReactionEvent: Optional[CallReactionEvent] = None
    CallRecordingStartedEvent: Optional[CallRecordingStartedEvent] = None
    CallRecordingStoppedEvent: Optional[CallRecordingStoppedEvent] = None
    CallRejectedEvent: Optional[CallRejectedEvent] = None
    CallRingEvent: Optional[CallRingEvent] = None
    CallSessionEndedEvent: Optional[CallSessionEndedEvent] = None
    CallSessionParticipantJoinedEvent: Optional[
        CallSessionParticipantJoinedEvent
    ] = None
    CallSessionParticipantLeftEvent: Optional[CallSessionParticipantLeftEvent] = None
    CallSessionStartedEvent: Optional[CallSessionStartedEvent] = None
    CallUpdatedEvent: Optional[CallUpdatedEvent] = None
    ConnectedEvent: Optional[ConnectedEvent] = None
    ConnectionErrorEvent: Optional[ConnectionErrorEvent] = None
    CustomVideoEvent: Optional[CustomVideoEvent] = None
    HealthCheckEvent: Optional[HealthCheckEvent] = None
    PermissionRequestEvent: Optional[PermissionRequestEvent] = None
    UnblockedUserEvent: Optional[UnblockedUserEvent] = None
    UpdatedCallPermissionsEvent: Optional[UpdatedCallPermissionsEvent] = None
