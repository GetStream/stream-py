from dataclasses import dataclass
from typing import Optional, Dict, List
from datetime import datetime


@dataclass
class UserResponse:
    id: str
    created_at: datetime
    updated_at: datetime
    custom: Dict[str, str]
    role: str
    teams: List[str]
    deleted_at: Optional[datetime] = None
    image: Optional[str] = None
    name: Optional[str] = None
