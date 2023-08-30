from dataclasses import dataclass
from typing import Optional

from .model_event_notification_settings_request import (
    EventNotificationSettingsRequest,
)


@dataclass
class NotificationSettingsRequest:
    call_live_started: Optional[EventNotificationSettingsRequest] = None
    call_notification: Optional[EventNotificationSettingsRequest] = None
    call_ring: Optional[EventNotificationSettingsRequest] = None
    enabled: Optional[bool] = None
    session_started: Optional[EventNotificationSettingsRequest] = None

    @classmethod
    def from_dict(cls, data: dict) -> "NotificationSettingsRequest":
        data["call_live_started"] = (
            EventNotificationSettingsRequest.from_dict(data["call_live_started"])
            if data.get("call_live_started")
            else None
        )
        data["call_notification"] = (
            EventNotificationSettingsRequest.from_dict(data["call_notification"])
            if data.get("call_notification")
            else None
        )
        data["call_ring"] = (
            EventNotificationSettingsRequest.from_dict(data["call_ring"])
            if data.get("call_ring")
            else None
        )
        data["session_started"] = (
            EventNotificationSettingsRequest.from_dict(data["session_started"])
            if data.get("session_started")
            else None
        )
        return cls(**data)
