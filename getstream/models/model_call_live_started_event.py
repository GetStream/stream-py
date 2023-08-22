from dataclasses import dataclass
from datetime import datetime

from models.model_call_member_removed_event import CallResponse


@dataclass
class CallLiveStartedEvent:
    call: CallResponse
    call_cid: str
    created_at: datetime
    type: str
