from dataclasses import dataclass, field
from dataclasses_json import config, dataclass_json

from typing import List, Dict, Optional
from datetime import datetime


@dataclass_json
@dataclass
class UserResponse:
    teams: List[str] = field(metadata=config(field_name="teams"))
    updated_at: datetime = field(metadata=config(field_name="updated_at"))
    id: str = field(metadata=config(field_name="id"))
    role: str = field(metadata=config(field_name="role"))
    created_at: datetime = field(metadata=config(field_name="created_at"))
    custom: Dict[str, object] = field(metadata=config(field_name="custom"))
    deleted_at: Optional[datetime] = field(
        metadata=config(field_name="deleted_at"), default=None
    )
    name: Optional[str] = field(metadata=config(field_name="name"), default=None)
    image: Optional[str] = field(metadata=config(field_name="image"), default=None)
