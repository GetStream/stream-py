from dataclasses import dataclass
from datetime import datetime
from typing import List

from .model_call_notification_event import UserResponse


@dataclass
class PermissionRequestEvent:
    call_cid: str
    created_at: datetime
    permissions: List[str]
    type: str
    user: UserResponse

    @classmethod
    def from_dict(cls, data: dict) -> "PermissionRequestEvent":
        data["user"] = UserResponse.from_dict(data["user"])
        return cls(**data)
