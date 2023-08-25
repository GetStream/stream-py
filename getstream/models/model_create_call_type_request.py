from dataclasses import dataclass
from typing import Optional, Dict, List
from .model_call_settings_request import CallSettingsRequest

from .model_notification_settings_request import NotificationSettingsRequest


@dataclass
class CreateCallTypeRequest:
    grants: Optional[Dict[str, List[str]]] = None
    name: str
    notification_settings: Optional[NotificationSettingsRequest] = None
    settings: Optional[CallSettingsRequest] = None
