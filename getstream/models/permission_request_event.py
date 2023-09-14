from dataclasses import dataclass, field
from typing import Optional
from dataclasses_json import config, dataclass_json
from user_response import UserResponse


@dataclass_json
@dataclass
class PermissionRequestEvent:
    call_cid: str = field(metadata=config(field_name="call_cid"))
    created_at: str = field(metadata=config(field_name="created_at"))
    permissions: list[str] = field(metadata=config(field_name="permissions"))
    type: str = field(metadata=config(field_name="type"))
    user: UserResponse = field(metadata=config(field_name="user"))
