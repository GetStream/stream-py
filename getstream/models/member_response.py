from dataclasses import dataclass, field

from dataclasses_json import config, dataclass_json
from user_response import UserResponse


@dataclass_json
@dataclass
class MemberResponse:
    created_at: str = field(metadata=config(field_name="created_at"))
    custom: dict[str, object] = field(metadata=config(field_name="custom"))
    updated_at: str = field(metadata=config(field_name="updated_at"))
    user: UserResponse = field(metadata=config(field_name="user"))
    user_id: str = field(metadata=config(field_name="user_id"))
    deleted_at: Optional[str] = field(
        metadata=config(field_name="deleted_at"), default=None
    )
    role: Optional[str] = field(metadata=config(field_name="role"), default=None)
