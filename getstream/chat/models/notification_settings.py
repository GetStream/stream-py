# THIS FILE IS GENERATED FROM github.com/GetStream/protocol/tree/main/openapi-gen/templates/python/type.tmpl
from dataclasses import dataclass, field
from dataclasses_json import config, dataclass_json

from getstream.chat.models.event_notification_settings import EventNotificationSettings


@dataclass_json
@dataclass
class NotificationSettings:
    call_ring: EventNotificationSettings = field(
        metadata=config(field_name="call_ring")
    )
    enabled: bool = field(metadata=config(field_name="enabled"))
    session_started: EventNotificationSettings = field(
        metadata=config(field_name="session_started")
    )
    call_live_started: EventNotificationSettings = field(
        metadata=config(field_name="call_live_started")
    )
    call_notification: EventNotificationSettings = field(
        metadata=config(field_name="call_notification")
    )
