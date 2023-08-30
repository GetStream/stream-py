from dataclasses import dataclass
from datetime import datetime


@dataclass
class CallRecordingStoppedEvent:
    call_cid: str
    created_at: datetime
    type: str

    @classmethod
    def from_dict(cls, data: dict) -> "CallRecordingStoppedEvent":
        return cls(**data)
