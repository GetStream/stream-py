from dataclasses import dataclass
from typing import Dict, Any
from datetime import datetime

from models.model_call_notification_event import UserResponse


@dataclass
class CustomVideoEvent:
    call_cid: str
    created_at: datetime
    custom: Dict[str, Any]
    type: str
    user: UserResponse
