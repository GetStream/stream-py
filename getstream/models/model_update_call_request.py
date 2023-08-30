from dataclasses import dataclass
from typing import Optional, Dict, Any
from datetime import datetime

from .model_call_settings_request import CallSettingsRequest


@dataclass
class UpdateCallRequest:
    custom: Optional[Dict[str, Any]]
    settings_override: Optional[CallSettingsRequest]
    starts_at: Optional[datetime]

    @classmethod
    def from_dict(cls, data: dict) -> "UpdateCallRequest":
        data["settings_override"] = (
            CallSettingsRequest.from_dict(data["settings_override"])
            if data.get("settings_override")
            else None
        )
        data["starts_at"] = ()
        return cls(**data)
