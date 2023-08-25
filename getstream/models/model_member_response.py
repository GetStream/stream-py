from dataclasses import dataclass
from typing import Optional, Dict, Any
from datetime import datetime

from .model_user_response import UserResponse




@dataclass
class MemberResponse:
    created_at: datetime
    custom: Dict[str, Any]
    updated_at: datetime
    user: UserResponse
    user_id: str
    deleted_at: Optional[datetime] = None
    role: Optional[str] = None
