from dataclasses import dataclass
from datetime import datetime
from typing import Dict, List
from models.model_call_settings_response import CallSettingsResponse

from models.model_notification_settings import NotificationSettings


@dataclass
class CallTypeResponse:
    created_at: datetime
    grants: Dict[str, List[str]]
    name: str
    notification_settings: NotificationSettings
    settings: CallSettingsResponse
    updated_at: datetime
