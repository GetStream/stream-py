from typing import List
from dataclasses import dataclass

from models.model_member_request import MemberRequest


@dataclass
class UpdateCallMembersRequest:
    remove_members: List[str] = None
    update_members: List[MemberRequest] = None
