from dataclasses import dataclass
from datetime import datetime

from .model_own_user_response import OwnUserResponse


@dataclass
class ConnectedEvent:
    connection_id: str
    created_at: datetime
    me: OwnUserResponse
    type: str

    @classmethod
    def from_dict(cls, data: dict) -> "ConnectedEvent":
        data["created_at"] = datetime.fromisoformat(data["created_at"])
        data["me"] = OwnUserResponse.from_dict(data["me"])
        return cls(**data)
