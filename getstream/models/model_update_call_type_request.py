from dataclasses import dataclass
from typing import Optional, Dict, List
from models.model_call_settings_request import CallSettingsRequest
from models.model_create_call_type_request import NotificationSettingsRequest


@dataclass
class UpdateCallTypeRequest:
    grants: Optional[Dict[str, List[str]]] = None
    notification_settings: Optional[NotificationSettingsRequest] = None
    settings: Optional[CallSettingsRequest] = None
