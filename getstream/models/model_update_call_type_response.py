from dataclasses import dataclass
from datetime import datetime
from typing import Dict, List
from .model_call_settings_response import CallSettingsResponse

from .model_call_type_response import NotificationSettings


@dataclass
class UpdateCallTypeResponse:
    created_at: datetime
    duration: str
    grants: Dict[str, List[str]]
    name: str
    notification_settings: NotificationSettings
    settings: CallSettingsResponse
    updated_at: datetime

    @classmethod
    def from_dict(cls, data: dict) -> "UpdateCallTypeResponse":
        return cls(**data)
