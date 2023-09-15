from dataclasses import dataclass, field

from dataclasses_json import config, dataclass_json
from notification_settings import NotificationSettings
from call_settings_response import CallSettingsResponse


@dataclass_json
@dataclass
class UpdateCallTypeResponse:
    grants: dict[str, list[str]] = field(metadata=config(field_name="grants"))
    name: str = field(metadata=config(field_name="name"))
    notification_settings: NotificationSettings = field(
        metadata=config(field_name="notification_settings")
    )
    settings: CallSettingsResponse = field(metadata=config(field_name="settings"))
    updated_at: str = field(metadata=config(field_name="updated_at"))
    created_at: str = field(metadata=config(field_name="created_at"))
    duration: str = field(metadata=config(field_name="duration"))
