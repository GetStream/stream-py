from dataclasses import dataclass
from datetime import datetime
from typing import List

from models.model_call_notification_event import CallResponse


@dataclass
class CallMemberRemovedEvent:
    call: CallResponse
    call_cid: str
    created_at: datetime
    members: List[str]
    type: str
