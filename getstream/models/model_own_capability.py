from typing import Literal, List
from dataclasses import dataclass

OwnCapability = Literal[
    "block-users",
    "create-call",
    "create-reaction",
    "end-call",
    "join-backstage",
    "join-call",
    "join-ended-call",
    "mute-users",
    "read-call",
    "remove-call-member",
    "screenshare",
    "send-audio",
    "send-video",
    "start-broadcast-call",
    "start-record-call",
    "start-transcription-call",
    "stop-broadcast-call",
    "stop-record-call",
    "stop-transcription-call",
    "update-call",
    "update-call-member",
    "update-call-permissions",
    "update-call-settings",
]


@dataclass
class AllowedOwnCapabilityEnumValues:
    own_capabilities: List[OwnCapability]
