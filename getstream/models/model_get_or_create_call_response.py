from dataclasses import dataclass
from typing import List, Optional

from .model_user_response import UserResponse

from .model_member_response import MemberResponse
from .model_call_response import CallResponse

from .model_own_capability import OwnCapability


@dataclass
class GetOrCreateCallResponse:
    blocked_users: List[UserResponse]
    call: CallResponse
    created: bool
    duration: str
    members: List[MemberResponse]
    own_capabilities: List[OwnCapability]
    membership: Optional[MemberResponse] = None

    @classmethod
    def from_dict(cls, data: dict) -> "GetOrCreateCallResponse":
        data["call"] = CallResponse.from_dict(data["call"])
        if data.get("members"):
            data["members"] = [MemberResponse.from_dict(m) for m in data["members"]]
        if data.get("membership"):
            data["membership"] = MemberResponse.from_dict(data["membership"])
        data["blocked_users"] = [
            UserResponse.from_dict(bu) for bu in data["blocked_users"]
        ]
        data["own_capabilities"] = [
            OwnCapability.from_str(oc) for oc in data["own_capabilities"]
        ]
        return cls(**data)
