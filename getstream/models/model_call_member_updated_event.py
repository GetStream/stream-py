from dataclasses import dataclass
from typing import List
from datetime import datetime

from .model_call_response import CallResponse
from .model_call_notification_event import MemberResponse


@dataclass
class CallMemberUpdatedEvent:
    call: CallResponse
    call_cid: str
    created_at: datetime
    members: List[MemberResponse]
    type: str
