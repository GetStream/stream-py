from dataclasses import dataclass
from datetime import datetime

from models.model_call_notification_event import UserResponse


@dataclass
class CallEndedEvent:
    call_cid: str
    created_at: datetime
    type: str
    user: UserResponse
