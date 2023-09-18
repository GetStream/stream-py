from dataclasses import dataclass, field
from typing import Optional
from dataclasses_json import config, dataclass_json
from user_response import UserResponse


@dataclass_json
@dataclass
class BlockedUserEvent:
    call_cid: str = field(metadata=config(field_name="call_cid"))
    created_at: str = field(metadata=config(field_name="created_at"))
    type: str = field(metadata=config(field_name="type"))
    user: UserResponse = field(metadata=config(field_name="user"))
    blocked_by_user: Optional[UserResponse] = field(
        metadata=config(field_name="blocked_by_user"), default=None
    )
