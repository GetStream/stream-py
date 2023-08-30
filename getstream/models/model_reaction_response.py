from dataclasses import dataclass
from typing import Optional, Dict, Any

from .model_user_response import UserResponse


@dataclass
class ReactionResponse:
    type: str
    user: UserResponse
    custom: Optional[Dict[str, Any]] = None
    emoji_code: Optional[str] = None

    @classmethod
    def from_dict(cls, data: dict) -> "ReactionResponse":
        data["user"] = UserResponse.from_dict(data["user"])
        return cls(**data)
