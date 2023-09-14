from dataclasses import dataclass, field
from typing import Optional
from dataclasses_json import config, dataclass_json
from event_notification_settings import EventNotificationSettings
from event_notification_settings import EventNotificationSettings
from event_notification_settings import EventNotificationSettings
from event_notification_settings import EventNotificationSettings


@dataclass_json
@dataclass
class NotificationSettings:
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
    call_ring: EventNotificationSettings = field(
        metadata=config(field_name="call_ring")
    )
