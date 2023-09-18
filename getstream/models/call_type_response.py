from dataclasses import dataclass, field
from dataclasses_json import config, dataclass_json

from typing import List, Dict
from datetime import datetime
from getstream.models.notification_settings import NotificationSettings
from getstream.models.call_settings_response import CallSettingsResponse


@dataclass_json
@dataclass
class CallTypeResponse:
    created_at: datetime = field(metadata=config(field_name="created_at"))
    grants: Dict[str, List[str]] = field(metadata=config(field_name="grants"))
    name: str = field(metadata=config(field_name="name"))
    notification_settings: NotificationSettings = field(
        metadata=config(field_name="notification_settings")
    )
    settings: CallSettingsResponse = field(metadata=config(field_name="settings"))
    updated_at: datetime = field(metadata=config(field_name="updated_at"))
