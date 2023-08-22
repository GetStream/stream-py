from dataclasses import dataclass
from typing import List
from datetime import datetime

from models.model_call_notification_event import CallResponse, MemberResponse


@dataclass
class CallMemberUpdatedEvent:
    call: CallResponse
    call_cid: str
    created_at: datetime
    members: List[MemberResponse]
    type: str
