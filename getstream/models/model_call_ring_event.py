from dataclasses import dataclass
from datetime import datetime
from typing import List


from .model_member_response import MemberResponse
from .model_user_response import UserResponse
from .model_call_response from .model_call_response import CallResponse


@dataclass
class CallRingEvent:
    call: CallResponse
    call_cid: str
    created_at: datetime
    members: List[MemberResponse]
    session_id: str
    type: str
    user: UserResponse
