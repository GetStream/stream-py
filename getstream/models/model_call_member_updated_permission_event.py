from dataclasses import dataclass
from typing import List, Dict
from datetime import datetime

from .model_call_response import CallResponse, MemberResponse


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
        data["created_at"] = datetime.fromisoformat(data["created_at"])
        data["members"] = [
            MemberResponse.from_dict(member) for member in data["members"]
        ]
        return cls(**data)
