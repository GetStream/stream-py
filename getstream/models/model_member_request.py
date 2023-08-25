from dataclasses import dataclass
from typing import Optional, Dict, Any


@dataclass
class MemberRequest:
    user_id: str
    custom: Optional[Dict[str, Any]] = None
    role: Optional[str] = None
