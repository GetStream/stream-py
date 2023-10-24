# THIS FILE IS GENERATED FROM github.com/GetStream/protocol/tree/main/openapi-gen/templates/python/type.tmpl
from enum import Enum


class OwnCapability(Enum):
    BLOCK_USERS = "block-users"
    CREATE_CALL = "create-call"
    CREATE_REACTION = "create-reaction"
    END_CALL = "end-call"
    JOIN_BACKSTAGE = "join-backstage"
    JOIN_CALL = "join-call"
    JOIN_ENDED_CALL = "join-ended-call"
    MUTE_USERS = "mute-users"
    PIN_FOR_EVERYONE = "pin-for-everyone"
    READ_CALL = "read-call"
    REMOVE_CALL_MEMBER = "remove-call-member"
    SCREENSHARE = "screenshare"
    SEND_AUDIO = "send-audio"
    SEND_VIDEO = "send-video"
    START_BROADCAST_CALL = "start-broadcast-call"
    START_RECORD_CALL = "start-record-call"
    START_TRANSCRIPTION_CALL = "start-transcription-call"
    STOP_BROADCAST_CALL = "stop-broadcast-call"
    STOP_RECORD_CALL = "stop-record-call"
    STOP_TRANSCRIPTION_CALL = "stop-transcription-call"
    UPDATE_CALL = "update-call"
    UPDATE_CALL_MEMBER = "update-call-member"
    UPDATE_CALL_PERMISSIONS = "update-call-permissions"
    UPDATE_CALL_SETTINGS = "update-call-settings"

    @classmethod
    def from_str(cls, value: str) -> "OwnCapability":
        try:
            return cls(value)
        except ValueError:
            raise ValueError(f"'{value}' is not a valid OwnCapability")

    def to_str(self) -> str:
        return self.value
