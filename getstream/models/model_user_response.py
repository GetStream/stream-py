from dataclasses import dataclass
from typing import Optional, Dict, List
from datetime import datetime


@dataclass
class UserResponse:
    created_at: datetime
    custom: Dict[str, str]
    deleted_at: Optional[datetime] = None
    id: str
    image: Optional[str] = None
    name: Optional[str] = None
    role: str
    teams: List[str]
    updated_at: datetime
