from dataclasses import dataclass
from typing import Optional

from .model_apns_request import APNSRequest


@dataclass
class EventNotificationSettingsRequest:
    apns: Optional[APNSRequest]
    enabled: Optional[bool]
