from dataclasses import dataclass

from .model_event_notification_settings import EventNotificationSettings


@dataclass
class NotificationSettings:
    call_live_started: EventNotificationSettings
    call_notification: EventNotificationSettings
    call_ring: EventNotificationSettings
    enabled: bool
    session_started: EventNotificationSettings
