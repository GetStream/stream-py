from dataclasses import dataclass
from datetime import datetime

from .model_call_response from .model_call_response import CallResponse


@dataclass
class CallSessionStartedEvent:
    call: CallResponse
    call_cid: str
    created_at: datetime
    session_id: str
    type: str
