from dataclasses import dataclass, field

from dataclasses_json import config, dataclass_json


@dataclass_json
@dataclass
class UserResponse:
    created_at: str = field(metadata=config(field_name="created_at"))
    id: str = field(metadata=config(field_name="id"))
    teams: list[str] = field(metadata=config(field_name="teams"))
    updated_at: str = field(metadata=config(field_name="updated_at"))
    custom: dict[str, object] = field(metadata=config(field_name="custom"))
    role: str = field(metadata=config(field_name="role"))
    image: Optional[str] = field(metadata=config(field_name="image"), default=None)
    deleted_at: Optional[str] = field(
        metadata=config(field_name="deleted_at"), default=None
    )
    name: Optional[str] = field(metadata=config(field_name="name"), default=None)
