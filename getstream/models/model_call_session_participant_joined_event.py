from dataclasses import dataclass
from datetime import datetime

from .model_call_participant_response import CallParticipantResponse


@dataclass
class CallSessionParticipantJoinedEvent:
    call_cid: str
    created_at: datetime
    participant: CallParticipantResponse
    session_id: str
    type: str

    @classmethod
    def from_dict(cls, data: dict) -> "CallSessionParticipantJoinedEvent":
        data["created_at"] = datetime.fromisoformat(data["created_at"])
        data["participant"] = CallParticipantResponse.from_dict(data["participant"])
        return cls(**data)
