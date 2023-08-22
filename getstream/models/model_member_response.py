from dataclasses import dataclass
from typing import Optional, Dict, Any
from datetime import datetime

from models.model_call_notification_event import UserResponse


@dataclass
class MemberResponse:
    created_at: datetime
    custom: Dict[str, Any]
    deleted_at: Optional[datetime] = None
    role: Optional[str] = None
    updated_at: datetime
    user: UserResponse
    user_id: str
