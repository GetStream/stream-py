from dataclasses import dataclass

from models.model_call_notification_event import UserResponse


@dataclass
class CreateGuestResponse:
    access_token: str
    duration: str
    user: UserResponse
