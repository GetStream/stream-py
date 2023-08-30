from typing import Optional, List, Dict, Any
from dataclasses import dataclass


@dataclass
class UserRequest:
    id: str
    custom: Optional[Dict[str, Any]] = None
    image: Optional[str] = None
    name: Optional[str] = None
    role: Optional[str] = None
    teams: Optional[List[str]] = None

    @classmethod
    def from_dict(cls, data: dict) -> "UserRequest":
        return cls(**data)
