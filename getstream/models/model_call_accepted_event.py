from dataclasses import dataclass
from datetime import datetime
from models.model_call_member_removed_event import CallResponse

from models.model_call_notification_event import UserResponse


@dataclass
class CallAcceptedEvent:
    call: CallResponse
    call_cid: str
    created_at: datetime
    type: str
    user: UserResponse
