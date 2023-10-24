# THIS FILE IS GENERATED FROM github.com/GetStream/protocol/tree/main/openapi-gen/templates/python/type.tmpl
from dataclasses import dataclass, field
from dataclasses_json import config, dataclass_json

from typing import Optional
from getstream.models.event_notification_settings_request import (
    EventNotificationSettingsRequest,
)


@dataclass_json
@dataclass
class NotificationSettingsRequest:
    call_live_started: Optional[EventNotificationSettingsRequest] = field(
        metadata=config(field_name="call_live_started"), default=None
    )
    call_notification: Optional[EventNotificationSettingsRequest] = field(
        metadata=config(field_name="call_notification"), default=None
    )
    call_ring: Optional[EventNotificationSettingsRequest] = field(
        metadata=config(field_name="call_ring"), default=None
    )
    enabled: Optional[bool] = field(metadata=config(field_name="enabled"), default=None)
    session_started: Optional[EventNotificationSettingsRequest] = field(
        metadata=config(field_name="session_started"), default=None
    )
