from dataclasses import dataclass
from typing import Optional
from datetime import datetime

from .model_call_notification_event import UserResponse


@dataclass
class BlockedUserEvent:
    call_cid: str
    created_at: datetime
    type: str
    user: UserResponse
    blocked_by_user: Optional[UserResponse] = None

    @classmethod
    def from_dict(cls, data: dict) -> "BlockedUserEvent":
        if data["blocked_by_user"] is not None:
            data["blocked_by_user"] = UserResponse.from_dict(data["blocked_by_user"])

        data["user"] = UserResponse.from_dict(data["user"])
        return cls(**data)
