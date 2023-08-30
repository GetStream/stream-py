from dataclasses import dataclass
from datetime import datetime


@dataclass
class HealthCheckEvent:
    connection_id: str
    created_at: datetime
    type: str

    @classmethod
    def from_dict(cls, data: dict) -> "HealthCheckEvent":
        data["created_at"] = datetime.fromisoformat(data["created_at"])
        return cls(**data)
