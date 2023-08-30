from dataclasses import dataclass
from datetime import datetime
from typing import List

from .model_user_response import UserResponse

from .model_member_response import MemberResponse
from .model_call_response import CallResponse


@dataclass
class CallNotificationEvent:
    call: CallResponse
    call_cid: str
    created_at: datetime
    members: List[MemberResponse]
    session_id: str
    type: str
    user: UserResponse

    @classmethod
    def from_dict(cls, data: dict) -> "CallNotificationEvent":
        data["call"] = CallResponse.from_dict(data["call"])

        data["members"] = [
            MemberResponse.from_dict(member) for member in data["members"]
        ]
        data["user"] = UserResponse.from_dict(data["user"])
        return cls(**data)
