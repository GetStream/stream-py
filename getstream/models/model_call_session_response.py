from dataclasses import dataclass
from typing import Optional, List, Dict
from datetime import datetime
from .model_call_participant_response import CallParticipantResponse


@dataclass
class CallSessionResponse:
    id: str
    accepted_by: Dict[str, datetime]
    participants: List[CallParticipantResponse]
    participants_count_by_role: Dict[str, int]
    rejected_by: Dict[str, datetime]
    started_at: Optional[datetime]
    ended_at: Optional[datetime]

    @classmethod
    def from_dict(cls, data: dict) -> "CallSessionResponse":
        data["participants"] = [
            CallParticipantResponse.from_dict(d) for d in data["participants"]
        ]
        return cls(**data)
