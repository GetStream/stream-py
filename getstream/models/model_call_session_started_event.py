from dataclasses import dataclass
from datetime import datetime

from .model_call_response import CallResponse


@dataclass
class CallSessionStartedEvent:
    call: CallResponse
    call_cid: str
    created_at: datetime
    session_id: str
    type: str

    @classmethod
    def from_dict(cls, data: dict) -> "CallSessionStartedEvent":
        data["call"] = CallResponse.from_dict(data["call"])

        return cls(**data)
