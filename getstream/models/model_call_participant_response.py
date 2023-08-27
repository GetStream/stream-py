from dataclasses import dataclass

from datetime import datetime

from .model_user_response import UserResponse


@dataclass
class CallParticipantResponse:
    joined_at: datetime
    role: str
    user: UserResponse
    user_session_id: str

    @classmethod
    def from_dict(cls, data: dict) -> "CallParticipantResponse":
        data["user"] = UserResponse.from_dict(data["user"])
        return cls(**data)
