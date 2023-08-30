from dataclasses import dataclass
from datetime import datetime
from typing import Optional


@dataclass
class ConnectionErrorEvent:
    connection_id: str
    created_at: datetime
    error: Optional[str] = None
    type: str

    @classmethod
    def from_dict(cls, data: dict) -> "ConnectionErrorEvent":
        data["created_at"] = datetime.fromisoformat(data["created_at"])
        return cls(**data)
