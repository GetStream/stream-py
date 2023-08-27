from dataclasses import dataclass

from .model_event_notification_settings import EventNotificationSettings


@dataclass
class NotificationSettings:
    call_live_started: EventNotificationSettings
    call_notification: EventNotificationSettings
    call_ring: EventNotificationSettings
    enabled: bool
    session_started: EventNotificationSettings

    @classmethod
    def from_dict(cls, data: dict) -> "NotificationSettings":
        data["call_live_started"] = EventNotificationSettings.from_dict(
            data["call_live_started"]
        )
        data["call_notification"] = EventNotificationSettings.from_dict(
            data["call_notification"]
        )
        data["call_ring"] = EventNotificationSettings.from_dict(data["call_ring"])
        data["session_started"] = EventNotificationSettings.from_dict(
            data["session_started"]
        )
        return cls(**data)
