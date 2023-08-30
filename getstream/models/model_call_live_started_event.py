from dataclasses import dataclass
from datetime import datetime

from .model_call_response import CallResponse


@dataclass
class CallLiveStartedEvent:
    call: CallResponse
    call_cid: str
    created_at: datetime
    type: str

    @classmethod
    def from_dict(cls, data: dict) -> "CallLiveStartedEvent":
        data["call"] = CallResponse.from_dict(data["call"])
        data["created_at"] = datetime.fromisoformat(data["created_at"])
        return cls(**data)
