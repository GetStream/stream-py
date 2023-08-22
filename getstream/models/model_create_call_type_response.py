from dataclasses import dataclass
from typing import Dict, List
from datetime import datetime

from models.model_call_settings_response import CallSettingsResponse
from models.model_call_type_response import NotificationSettings


@dataclass
class CreateCallTypeResponse:
    created_at: datetime
    duration: str
    grants: Dict[str, List[str]]
    name: str
    notification_settings: NotificationSettings
    settings: CallSettingsResponse
    updated_at: datetime
