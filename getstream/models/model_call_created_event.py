from dataclasses import dataclass
from typing import List
from datetime import datetime

from models.model_call_member_removed_event import CallResponse
from models.model_call_notification_event import MemberResponse


@dataclass
class CallCreatedEvent:
    call: CallResponse
    call_cid: str
    created_at: datetime
    members: List[MemberResponse]
    type: str
