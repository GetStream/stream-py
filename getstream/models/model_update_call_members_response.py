from dataclasses import dataclass
from typing import List

from .model_call_notification_event import MemberResponse


@dataclass
class UpdateCallMembersResponse:
    duration: str
    members: List[MemberResponse]

    @classmethod
    def from_dict(cls, data: dict) -> "UpdateCallMembersResponse":
        if data.get("members"):
            data["members"] = [MemberResponse.from_dict(d) for d in data["members"]]
        return cls(**data)
