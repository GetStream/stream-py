from datetime import datetime
from dataclasses import dataclass


@dataclass
class CallBroadcastingStoppedEvent:
    call_cid: str
    created_at: datetime
    type: str

    @classmethod
    def from_dict(cls, data: dict) -> "CallBroadcastingStoppedEvent":
        data["created_at"] = datetime.fromisoformat(data["created_at"])
        return cls(**data)
