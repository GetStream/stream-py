from dataclasses import dataclass
from typing import Optional, Dict, Any


@dataclass
class MemberRequest:
    user_id: str
    custom: Optional[Dict[str, Any]] = None
    role: Optional[str] = None

    @classmethod
    def from_dict(cls, data: dict) -> "MemberRequest":
        return cls(**data)
