from dataclasses import dataclass

from .model_apns import APNS


@dataclass
class EventNotificationSettings:
    apns: APNS
    enabled: bool
