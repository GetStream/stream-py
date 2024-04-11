# THIS FILE IS GENERATED FROM github.com/GetStream/protocol/tree/main/openapi-gen/templates/python/type.tmpl
from typing import Final, ClassVar, Optional


class OwnCapability:
    BLOCK_USERS: Final[str] = "block-users"
    CREATE_CALL: Final[str] = "create-call"
    CREATE_REACTION: Final[str] = "create-reaction"
    END_CALL: Final[str] = "end-call"
    JOIN_BACKSTAGE: Final[str] = "join-backstage"
    JOIN_CALL: Final[str] = "join-call"
    JOIN_ENDED_CALL: Final[str] = "join-ended-call"
    MUTE_USERS: Final[str] = "mute-users"
    PIN_FOR_EVERYONE: Final[str] = "pin-for-everyone"
    READ_CALL: Final[str] = "read-call"
    REMOVE_CALL_MEMBER: Final[str] = "remove-call-member"
    SCREENSHARE: Final[str] = "screenshare"
    SEND_AUDIO: Final[str] = "send-audio"
    SEND_VIDEO: Final[str] = "send-video"
    START_BROADCAST_CALL: Final[str] = "start-broadcast-call"
    START_RECORD_CALL: Final[str] = "start-record-call"
    START_TRANSCRIPTION_CALL: Final[str] = "start-transcription-call"
    STOP_BROADCAST_CALL: Final[str] = "stop-broadcast-call"
    STOP_RECORD_CALL: Final[str] = "stop-record-call"
    STOP_TRANSCRIPTION_CALL: Final[str] = "stop-transcription-call"
    UPDATE_CALL: Final[str] = "update-call"
    UPDATE_CALL_MEMBER: Final[str] = "update-call-member"
    UPDATE_CALL_PERMISSIONS: Final[str] = "update-call-permissions"
    UPDATE_CALL_SETTINGS: Final[str] = "update-call-settings"
    ENABLE_NOISE_CANCELLATION: Final[str] = "enable-noise-cancellation"

    _values: "ClassVar[dict[str, str]]" = {
        k: v for k, v in vars().items() if not k.startswith("_")
    }

    @classmethod
    def from_str(cls, value: str) -> Optional[str]:
        """Return the corresponding constant value for a given string, or None if not found."""
        return cls._values.get(value.upper(), None)

    @staticmethod
    def to_str(value: str) -> Optional[str]:
        """Return the string representation of a constant value, or None if the value is not valid."""
        if value in OwnCapability._values.values():
            return value
        return None
