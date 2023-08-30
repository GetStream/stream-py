from datetime import datetime
from dataclasses import dataclass


@dataclass
class CallBroadcastingStoppedEvent:
    call_cid: str
    created_at: datetime
    type: str

    @classmethod
    def from_dict(cls, data: dict) -> "CallBroadcastingStoppedEvent":
        return cls(**data)
