from datetime import datetime
from typing import List, Optional, Dict, Any
from dataclasses import dataclass

from .model_device import Device


@dataclass
class OwnUserResponse:
    created_at: datetime
    custom: Dict[str, Any]
    deleted_at: Optional[datetime] = None
    devices: List[Device]
    id: str
    image: Optional[str] = None
    name: Optional[str] = None
    role: str
    teams: List[str]
    updated_at: datetime

    @classmethod
    def from_dict(cls, data: dict) -> "OwnUserResponse":
        data["custom"] = data.get("custom", {})

        if data.get("devices"):
            data["devices"] = [Device.from_dict(d) for d in data["devices"]]

        return cls(**data)
