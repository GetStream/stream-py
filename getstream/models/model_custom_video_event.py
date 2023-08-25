from dataclasses import dataclass
from typing import Dict, Any
from datetime import datetime




@dataclass
class CustomVideoEvent:
    from .model_user_response import UserResponse
    call_cid: str
    created_at: datetime
    custom: Dict[str, Any]
    type: str
    user: UserResponse
