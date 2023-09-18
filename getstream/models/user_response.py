from dataclasses import dataclass, field
from dataclasses_json import config, dataclass_json

from typing import Dict, List, Optional
from datetime import datetime


@dataclass_json
@dataclass
class UserResponse:
    id: str = field(metadata=config(field_name="id"))
    teams: List[str] = field(metadata=config(field_name="teams"))
    created_at: datetime = field(metadata=config(field_name="created_at"))
    custom: Dict[str, object] = field(metadata=config(field_name="custom"))
    updated_at: datetime = field(metadata=config(field_name="updated_at"))
    role: str = field(metadata=config(field_name="role"))
    image: Optional[str] = field(metadata=config(field_name="image"), default=None)
    name: Optional[str] = field(metadata=config(field_name="name"), default=None)
    deleted_at: Optional[datetime] = field(
        metadata=config(field_name="deleted_at"), default=None
    )
