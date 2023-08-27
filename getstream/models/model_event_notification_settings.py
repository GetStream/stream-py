from dataclasses import dataclass

from .model_apns import APNS


@dataclass
class EventNotificationSettings:
    apns: APNS
    enabled: bool

    @classmethod
    def from_dict(cls, data: dict) -> "EventNotificationSettings":
        data["apns"] = APNS.from_dict(data["apns"])
        return cls(**data)
