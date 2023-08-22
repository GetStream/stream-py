from dataclasses import dataclass
from typing import Optional, Dict, List
from models.model_call_settings_request import CallSettingsRequest

from models.model_notification_settings_request import NotificationSettingsRequest


@dataclass
class CreateCallTypeRequest:
    grants: Optional[Dict[str, List[str]]]
    name: str
    notification_settings: Optional[NotificationSettingsRequest]
    settings: Optional[CallSettingsRequest]
