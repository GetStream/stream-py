from typing import Optional, Dict, Any
from dataclasses import dataclass


@dataclass
class SendReactionRequest:
    custom: Optional[Dict[str, Any]] = None
    emoji_code: Optional[str] = None
    type: str = ""
