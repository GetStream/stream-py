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