from dataclasses import dataclass
from datetime import datetime
from typing import List


from .model_member_response import MemberResponse
from .model_user_response import UserResponse
from .model_call_response import CallResponse


@dataclass
class CallRingEvent:
    call: CallResponse
    call_cid: str
    created_at: datetime
    members: List[MemberResponse]
    session_id: str
    type: str
    user: UserResponse

    @classmethod
    def from_dict(cls, data: dict) -> "CallRingEvent":
        data["call"] = CallResponse.from_dict(data["call"])
        data["created_at"] = datetime.fromisoformat(data["created_at"])
        if data.get("members"):
            data["members"] = [
                MemberResponse.from_dict(member) for member in data["members"]
            ]
        data["user"] = UserResponse.from_dict(data["user"])
        return cls(**data)
