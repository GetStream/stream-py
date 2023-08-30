from dataclasses import dataclass
from typing import Optional, Dict, List
from .model_call_settings_request import CallSettingsRequest
from .model_create_call_type_request import NotificationSettingsRequest


@dataclass
class UpdateCallTypeRequest:
    grants: Optional[Dict[str, List[str]]] = None
    notification_settings: Optional[NotificationSettingsRequest] = None
    settings: Optional[CallSettingsRequest] = None

    @classmethod
    def from_dict(cls, data: dict) -> "UpdateCallTypeRequest":
        data["notification_settings"] = (
            NotificationSettingsRequest.from_dict(data["notification_settings"])
            if data.get("notification_settings")
            else None
        )
        data["settings"] = (
            CallSettingsRequest.from_dict(data["settings"])
            if data.get("settings")
            else None
        )
        return cls(**data)
