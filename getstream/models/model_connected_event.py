from dataclasses import dataclass
from datetime import datetime

from .model_own_user_response import OwnUserResponse


@dataclass
class ConnectedEvent:
    connection_id: str
    created_at: datetime
    me: OwnUserResponse
    type: str
