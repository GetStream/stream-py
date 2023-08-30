from dataclasses import dataclass
from typing import Optional


@dataclass
class WSClientEvent:
    connection_id: Optional[str] = None

    @classmethod
    def from_dict(cls, data: dict) -> "WSClientEvent":
        return cls(**data)
