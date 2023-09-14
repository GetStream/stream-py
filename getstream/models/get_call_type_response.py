from dataclasses import dataclass, field
from typing import Optional
from dataclasses_json import config, dataclass_json
from call_settings_response import CallSettingsResponse
from notification_settings import NotificationSettings


@dataclass_json
@dataclass
class GetCallTypeResponse:
    notification_settings: NotificationSettings = field(
        metadata=config(field_name="notification_settings")
    )
    settings: CallSettingsResponse = field(metadata=config(field_name="settings"))
    updated_at: str = field(metadata=config(field_name="updated_at"))
    created_at: str = field(metadata=config(field_name="created_at"))
    duration: str = field(metadata=config(field_name="duration"))
    grants: dict[str, list[str]] = field(metadata=config(field_name="grants"))
    name: str = field(metadata=config(field_name="name"))
