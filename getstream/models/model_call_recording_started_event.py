from dataclasses import dataclass
from datetime import datetime


@dataclass
class CallRecordingStartedEvent:
    call_cid: str
    created_at: datetime
    type: str

    @classmethod
    def from_dict(cls, data: dict) -> "CallRecordingStartedEvent":
        data["created_at"] = datetime.fromisoformat(data["created_at"])
        return cls(**data)
