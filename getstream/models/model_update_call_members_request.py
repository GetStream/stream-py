from typing import List
from dataclasses import dataclass

from .model_member_request import MemberRequest


@dataclass
class UpdateCallMembersRequest:
    remove_members: List[str] = None
    update_members: List[MemberRequest] = None

    @classmethod
    def from_dict(cls, data: dict) -> "UpdateCallMembersRequest":
        if data.get("update_members"):
            data["update_members"] = [
                MemberRequest.from_dict(d) for d in data["update_members"]
            ]
        return cls(**data)
