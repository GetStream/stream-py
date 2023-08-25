from dataclasses import dataclass
from typing import Optional, Dict, Any


@dataclass
class MemberRequest:
    custom: Optional[Dict[str, Any]] = None
    role: Optional[str] = None
    user_id: str
