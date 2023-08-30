from dataclasses import dataclass
from typing import List, Dict
from datetime import datetime

from .model_member_response import MemberResponse

from .model_call_response import CallResponse


@dataclass
class CallMemberUpdatedPermissionEvent:
    call: CallResponse
    call_cid: str
    capabilities_by_role: Dict[str, List[str]]
    created_at: datetime
    members: List[MemberResponse]
    type: str

    @classmethod
    def from_dict(cls, data: dict) -> "CallMemberUpdatedPermissionEvent":
        data["call"] = CallResponse.from_dict(data["call"])

        data["members"] = [
            MemberResponse.from_dict(member) for member in data["members"]
        ]
        return cls(**data)
