from dataclasses import dataclass
from datetime import datetime
from typing import List

from models.model_call_response import CallResponse
from models.model_member_response import MemberResponse
from models.model_user_response import UserResponse


@dataclass
class CallRingEvent:
    call: CallResponse
    call_cid: str
    created_at: datetime
    members: List[MemberResponse]
    session_id: str
    type: str
    user: UserResponse
