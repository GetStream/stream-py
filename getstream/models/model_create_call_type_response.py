from dataclasses import dataclass
from typing import Dict, List
from datetime import datetime

from .model_call_settings_response import CallSettingsResponse
from .model_call_type_response import NotificationSettings


@dataclass
class CreateCallTypeResponse:
    created_at: datetime
    duration: str
    grants: Dict[str, List[str]]
    name: str
    notification_settings: NotificationSettings
    settings: CallSettingsResponse
    updated_at: datetime

    @classmethod
    def from_dict(cls, data: dict) -> "CreateCallTypeResponse":
        data["notification_settings"] = NotificationSettings.from_dict(
            data["notification_settings"]
        )
        data["settings"] = CallSettingsResponse.from_dict(data["settings"])
        data["created_at"] = datetime.fromisoformat(data["created_at"])
        data["updated_at"] = datetime.fromisoformat(data["updated_at"])
        return cls(**data)
