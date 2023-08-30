from dataclasses import dataclass
from typing import List
from datetime import datetime

from .model_call_response import CallResponse
from .model_call_notification_event import MemberResponse


@dataclass
class CallMemberUpdatedEvent:
    call: CallResponse
    call_cid: str
    created_at: datetime
    members: List[MemberResponse]
    type: str

    @classmethod
    def from_dict(cls, data: dict) -> "CallMemberUpdatedEvent":
        data["call"] = CallResponse.from_dict(data["call"])
        data["created_at"] = datetime.fromisoformat(data["created_at"])
        data["members"] = [
            MemberResponse.from_dict(member) for member in data["members"]
        ]
        return cls(**data)
