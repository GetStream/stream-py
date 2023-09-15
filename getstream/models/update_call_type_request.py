from dataclasses import dataclass, field

from dataclasses_json import config, dataclass_json
from notification_settings_request import NotificationSettingsRequest
from call_settings_request import CallSettingsRequest


@dataclass_json
@dataclass
class UpdateCallTypeRequest:
    grants: Optional[dict[str, list[str]]] = field(
        metadata=config(field_name="grants"), default=None
    )
    notification_settings: Optional[NotificationSettingsRequest] = field(
        metadata=config(field_name="notification_settings"), default=None
    )
    settings: Optional[CallSettingsRequest] = field(
        metadata=config(field_name="settings"), default=None
    )
