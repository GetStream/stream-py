from dataclasses import dataclass
from datetime import datetime
from typing import List, Dict
from .model_call_settings_response import CallSettingsResponse

from .model_call_type_response import NotificationSettings


@dataclass
class GetCallTypeResponse:
    created_at: datetime
    duration: str
    grants: Dict[str, List[str]]
    name: str
    notification_settings: NotificationSettings
    settings: CallSettingsResponse
    updated_at: datetime

    @classmethod
    def from_dict(cls, data: dict) -> "GetCallTypeResponse":
        return cls(**data)