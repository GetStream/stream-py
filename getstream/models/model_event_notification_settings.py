from dataclasses import dataclass

from models.model_apns import APNS


@dataclass
class EventNotificationSettings:
    apns: APNS
    enabled: bool
