from dataclasses import dataclass, field
from dataclasses_json import config, dataclass_json

from typing import List, Dict, Optional
from datetime import datetime
from getstream.models.device import Device


@dataclass_json
@dataclass
class OwnUserResponse:
    updated_at: datetime = field(metadata=config(field_name="updated_at"))
    devices: List[Device] = field(metadata=config(field_name="devices"))
    role: str = field(metadata=config(field_name="role"))
    teams: List[str] = field(metadata=config(field_name="teams"))
    created_at: datetime = field(metadata=config(field_name="created_at"))
    custom: Dict[str, object] = field(metadata=config(field_name="custom"))
    id: str = field(metadata=config(field_name="id"))
    deleted_at: Optional[datetime] = field(
        metadata=config(field_name="deleted_at"), default=None
    )
    image: Optional[str] = field(metadata=config(field_name="image"), default=None)
    name: Optional[str] = field(metadata=config(field_name="name"), default=None)
