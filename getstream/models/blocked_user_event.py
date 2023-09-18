from dataclasses import dataclass, field
from dataclasses_json import config, dataclass_json

from typing import Optional
from datetime import datetime
from getstream.models.user_response import UserResponse


@dataclass_json
@dataclass
class BlockedUserEvent:
    created_at: datetime = field(metadata=config(field_name="created_at"))
    type: str = field(metadata=config(field_name="type"))
    user: UserResponse = field(metadata=config(field_name="user"))
    call_cid: str = field(metadata=config(field_name="call_cid"))
    blocked_by_user: Optional[UserResponse] = field(
        metadata=config(field_name="blocked_by_user"), default=None
    )
