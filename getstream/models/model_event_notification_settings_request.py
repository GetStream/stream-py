from dataclasses import dataclass
from typing import Optional

from .model_apns_request import APNSRequest


@dataclass
class EventNotificationSettingsRequest:
    apns: Optional[APNSRequest]
    enabled: Optional[bool]

    @classmethod
    def from_dict(cls, data: dict) -> "EventNotificationSettingsRequest":
        if data.get("apns"):
            data["apns"] = APNSRequest.from_dict(data["apns"])
        return cls(**data)
