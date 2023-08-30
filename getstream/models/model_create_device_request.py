from dataclasses import dataclass
from typing import Optional

from .model_user_request import UserRequest


@dataclass
class CreateDeviceRequest:
    id: Optional[str] = None
    push_provider: Optional[str] = None
    push_provider_name: Optional[str] = None
    user: Optional[UserRequest] = None
    user_id: Optional[str] = None
    voip_token: Optional[bool] = None

    @classmethod
    def from_dict(cls, data: dict) -> "CreateDeviceRequest":
        if data.get("user"):
            data["user"] = UserRequest.from_dict(data["user"])
        return cls(**data)
