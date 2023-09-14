from dataclasses import dataclass, field
from typing import Optional
from dataclasses_json import config, dataclass_json
from notification_settings_request import NotificationSettingsRequest
from call_settings_request import CallSettingsRequest


@dataclass_json
@dataclass
class CreateCallTypeRequest:
    name: str = field(metadata=config(field_name="name"))
    grants: Optional[dict[str, list[str]]] = field(
        metadata=config(field_name="grants"), default=None
    )
    notification_settings: Optional[NotificationSettingsRequest] = field(
        metadata=config(field_name="notification_settings"), default=None
    )
    settings: Optional[CallSettingsRequest] = field(
        metadata=config(field_name="settings"), default=None
    )
