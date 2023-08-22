from dataclasses import dataclass
from datetime import datetime
from typing import List

from models.model_call_response import CallResponse
from models.model_call_ring_event import MemberResponse, UserResponse


@dataclass
class CallNotificationEvent:
    call: CallResponse
    call_cid: str
    created_at: datetime
    members: List[MemberResponse]
    session_id: str
    type: str
    user: UserResponse
