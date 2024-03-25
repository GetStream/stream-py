# THIS FILE IS GENERATED FROM github.com/GetStream/protocol/tree/main/openapi-gen/templates/python/type.tmpl
from dataclasses import dataclass, field
from dataclasses_json import config, dataclass_json

from typing import List, Dict, Optional
from getstream.models.notification_settings_request import NotificationSettingsRequest
from getstream.models.call_settings_request import CallSettingsRequest


@dataclass_json
@dataclass
class CreateCallTypeRequest:
    name: str = field(metadata=config(field_name="name"))
    external_storage: Optional[str] = field(
        metadata=config(field_name="external_storage"), default=None
    )
    grants: Optional[Dict[str, List[str]]] = field(
        metadata=config(field_name="grants"), default=None
    )
    notification_settings: Optional[NotificationSettingsRequest] = field(
        metadata=config(field_name="notification_settings"), default=None
    )
    settings: Optional[CallSettingsRequest] = field(
        metadata=config(field_name="settings"), default=None
    )
