from dataclasses import dataclass
from typing import Any
from datetime import datetime

from models.model_call_notification_event import UserResponse


@dataclass
class UnblockedUserEvent:
    call_cid: str
    created_at: datetime
    type: str
    user: UserResponse
