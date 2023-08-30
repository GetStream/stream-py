from dataclasses import dataclass
from datetime import datetime

from .model_call_notification_event import UserResponse


@dataclass
class CallEndedEvent:
    call_cid: str
    created_at: datetime
    type: str
    user: UserResponse

    @classmethod
    def from_dict(cls, data: dict) -> "CallEndedEvent":
        data["user"] = UserResponse.from_dict(data["user"])
        return cls(**data)
