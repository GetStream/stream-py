from dataclasses import dataclass
from typing import Optional
from datetime import datetime


@dataclass
class Device:
    created_at: datetime
    disabled: Optional[bool]
    disabled_reason: Optional[str]
    id: str
    push_provider: str
    push_provider_name: Optional[str]
    voip: Optional[bool]

    @classmethod
    def from_dict(cls, data: dict) -> "Device":
        return cls(**data)
