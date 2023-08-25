from dataclasses import dataclass
from typing import List, Dict
from datetime import datetime

from .model_call_notification_event from .model_call_response import CallResponse, MemberResponse


@dataclass
class CallMemberUpdatedPermissionEvent:
    call: CallResponse
    call_cid: str
    capabilities_by_role: Dict[str, List[str]]
    created_at: datetime
    members: List[MemberResponse]
    type: str
