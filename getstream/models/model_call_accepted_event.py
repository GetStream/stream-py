from dataclasses import dataclass
from datetime import datetime

from .model_call_response import CallResponse

from .model_call_notification_event import UserResponse


@dataclass
class CallAcceptedEvent:
    call: CallResponse
    call_cid: str
    created_at: datetime
    type: str
    user: UserResponse

    @classmethod
    def from_dict(cls, data: dict) -> "CallAcceptedEvent":
        data["call"] = CallResponse.from_dict(data["call"])

        data["user"] = UserResponse.from_dict(data["user"])
        return cls(**data)
