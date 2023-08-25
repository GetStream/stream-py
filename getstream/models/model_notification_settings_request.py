from dataclasses import dataclass
from typing import Optional

from .model_event_notification_settings_request import (
    EventNotificationSettingsRequest,
)


@dataclass
class NotificationSettingsRequest:
    CallLiveStarted: Optional[EventNotificationSettingsRequest] = None
    CallNotification: Optional[EventNotificationSettingsRequest] = None
    CallRing: Optional[EventNotificationSettingsRequest] = None
    Enabled: Optional[bool] = None
    SessionStarted: Optional[EventNotificationSettingsRequest] = None
