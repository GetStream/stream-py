from dataclasses import dataclass, field

from dataclasses_json import config, dataclass_json
from user_response import UserResponse


@dataclass_json
@dataclass
class CustomVideoEvent:
    custom: dict[str, object] = field(metadata=config(field_name="custom"))
    type: str = field(metadata=config(field_name="type"))
    user: UserResponse = field(metadata=config(field_name="user"))
    call_cid: str = field(metadata=config(field_name="call_cid"))
    created_at: str = field(metadata=config(field_name="created_at"))
