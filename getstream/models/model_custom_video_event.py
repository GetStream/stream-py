from dataclasses import dataclass
from typing import Dict, Any
from datetime import datetime

from .model_user_response import UserResponse


@dataclass
class CustomVideoEvent:
    call_cid: str
    created_at: datetime
    custom: Dict[str, Any]
    type: str
    user: UserResponse

    @classmethod
    def from_dict(cls, data: dict) -> "CustomVideoEvent":
        data["created_at"] = datetime.fromisoformat(data["created_at"])
        data["user"] = UserResponse.from_dict(data["user"])
        return cls(**data)
