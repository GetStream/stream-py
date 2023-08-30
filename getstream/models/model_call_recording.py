from dataclasses import dataclass
from datetime import datetime


@dataclass
class CallRecording:
    end_time: datetime
    filename: str
    start_time: datetime
    url: str

    @classmethod
    def from_dict(cls, data: dict) -> "CallRecording":
        data["end_time"] = datetime.fromisoformat(data["end_time"])
        data["start_time"] = datetime.fromisoformat(data["start_time"])
        return cls(**data)
