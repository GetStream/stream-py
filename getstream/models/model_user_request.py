from typing import Optional, List, Dict, Any
from dataclasses import dataclass


@dataclass
class UserRequest:
    custom: Optional[Dict[str, Any]] = None
    id: str
    image: Optional[str] = None
    name: Optional[str] = None
    role: Optional[str] = None
    teams: Optional[List[str]] = None
