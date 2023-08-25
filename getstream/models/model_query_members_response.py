from dataclasses import dataclass
from typing import List, Optional

from .model_call_notification_event import MemberResponse


@dataclass
class QueryMembersResponse:
    duration: str
    members: List[MemberResponse]
    next: Optional[str]
    prev: Optional[str]
