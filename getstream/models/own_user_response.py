from dataclasses import dataclass, field
from typing import Optional
from dataclasses_json import config, dataclass_json
from device import Device


@dataclass_json
@dataclass
class OwnUserResponse:
    created_at: str = field(metadata=config(field_name="created_at"))
    custom: dict[str, object] = field(metadata=config(field_name="custom"))
    teams: list[str] = field(metadata=config(field_name="teams"))
    updated_at: str = field(metadata=config(field_name="updated_at"))
    devices: list[Device] = field(metadata=config(field_name="devices"))
    id: str = field(metadata=config(field_name="id"))
    role: str = field(metadata=config(field_name="role"))
    name: Optional[str] = field(metadata=config(field_name="name"), default=None)
    deleted_at: Optional[str] = field(
        metadata=config(field_name="deleted_at"), default=None
    )
    image: Optional[str] = field(metadata=config(field_name="image"), default=None)
