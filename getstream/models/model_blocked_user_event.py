from dataclasses import dataclass
from typing import Optional
from datetime import datetime

from models.model_call_notification_event import UserResponse


@dataclass
class BlockedUserEvent:
    blocked_by_user: Optional[UserResponse]
    call_cid: str
    created_at: datetime
    type: str
    user: UserResponse
