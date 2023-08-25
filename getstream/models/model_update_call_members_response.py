from dataclasses import dataclass
from typing import List

from .model_call_notification_event import MemberResponse


@dataclass
class UpdateCallMembersResponse:
    duration: str
    members: List[MemberResponse]
