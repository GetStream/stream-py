from dataclasses import dataclass
from typing import List, Optional

from .model_member_response import MemberResponse

from .model_user_response import UserResponse
from .model_call_response import CallResponse

from .model_own_capability import OwnCapability


@dataclass
class UpdateCallResponse:
    blocked_users: List[UserResponse]
    call: CallResponse
    duration: str
    members: List[MemberResponse]
    membership: Optional[MemberResponse]
    own_capabilities: List[OwnCapability]

    @classmethod
    def from_dict(cls, data: dict) -> "UpdateCallResponse":
        if data.get("blocked_users"):
            data["blocked_users"] = [
                UserResponse.from_dict(d) for d in data["blocked_users"]
            ]
        if data.get("call"):
            data["call"] = CallResponse.from_dict(data["call"])
        if data.get("members"):
            data["members"] = [MemberResponse.from_dict(d) for d in data["members"]]
        if data.get("membership"):
            data["membership"] = MemberResponse.from_dict(data["membership"])
        if data.get("own_capabilities"):
            data["own_capabilities"] = [
                OwnCapability.from_dict(d) for d in data["own_capabilities"]
            ]
        return cls(**data)
