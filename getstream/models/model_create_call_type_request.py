from dataclasses import dataclass
from typing import Optional, Dict, List
from .model_call_settings_request import CallSettingsRequest

from .model_notification_settings_request import NotificationSettingsRequest


@dataclass
class CreateCallTypeRequest:
    name: str
    grants: Optional[Dict[str, List[str]]] = None
    notification_settings: Optional[NotificationSettingsRequest] = None
    settings: Optional[CallSettingsRequest] = None

    @classmethod
    def from_dict(cls, data: dict) -> "CreateCallTypeRequest":
        if data.get("notification_settings"):
            data["notification_settings"] = NotificationSettingsRequest.from_dict(
                data["notification_settings"]
            )
        if data.get("settings"):
            data["settings"] = CallSettingsRequest.from_dict(data["settings"])
        return cls(**data)
