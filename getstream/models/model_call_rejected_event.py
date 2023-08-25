from dataclasses import dataclass

from datetime import datetime

from .model_call_response from .model_call_response import CallResponse
from .model_call_ring_event import UserResponse

@dataclass
class CallRejectedEvent:


    call: CallResponse
    call_cid: str
    created_at: datetime
    type: str
    user: UserResponse
