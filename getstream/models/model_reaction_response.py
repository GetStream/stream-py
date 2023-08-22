from dataclasses import dataclass
from typing import Optional, Dict, Any

from models.model_call_notification_event import UserResponse


@dataclass
class ReactionResponse:
    custom: Optional[Dict[str, Any]] = None
    emoji_code: Optional[str] = None
    type: str
    user: UserResponse
