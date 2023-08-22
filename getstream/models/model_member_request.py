from dataclasses import dataclass
from typing import Optional, Dict, Any


@dataclass
class MemberRequest:
    custom: Optional[Dict[str, Any]]
    role: Optional[str]
    user_id: str
