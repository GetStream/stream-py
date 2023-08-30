from dataclasses import dataclass

from .model_user_request import UserRequest


@dataclass
class CreateGuestRequest:
    user: UserRequest

    @classmethod
    def from_dict(cls, data: dict) -> "CreateGuestRequest":
        data["user"] = UserRequest.from_dict(data["user"])
        return cls(**data)
