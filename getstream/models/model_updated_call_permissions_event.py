from typing import List
from datetime import datetime
from dataclasses import dataclass

from .model_call_notification_event import UserResponse
from .model_own_capability import OwnCapability


@dataclass
class UpdatedCallPermissionsEvent:
    call_cid: str
    created_at: datetime
    own_capabilities: List[OwnCapability]
    type: str
    user: UserResponse

    @classmethod
    def from_dict(cls, data: dict) -> "UpdatedCallPermissionsEvent":
        data["created_at"] = datetime.fromisoformat(data["created_at"])
        data["own_capabilities"] = [
            OwnCapability.from_dict(d) for d in data["own_capabilities"]
        ]
        data["user"] = UserResponse.from_dict(data["user"])
        return cls(**data)
