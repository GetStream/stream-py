from dataclasses import dataclass

from .model_call_notification_event import UserResponse


@dataclass
class CreateGuestResponse:
    access_token: str
    duration: str
    user: UserResponse

    @classmethod
    def from_dict(cls, data: dict) -> "CreateGuestResponse":
        data["user"] = UserResponse.from_dict(data["user"])
        return cls(**data)
