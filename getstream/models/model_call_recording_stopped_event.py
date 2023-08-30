from dataclasses import dataclass
from datetime import datetime


@dataclass
class CallRecordingStoppedEvent:
    call_cid: str
    created_at: datetime
    type: str

    @classmethod
    def from_dict(cls, data: dict) -> "CallRecordingStoppedEvent":
        data["created_at"] = datetime.fromisoformat(data["created_at"])
        return cls(**data)
