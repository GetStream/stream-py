from dataclasses import dataclass, field
from dataclasses_json import config, dataclass_json

from typing import Dict, Optional
from datetime import datetime
from getstream.models.user_response import UserResponse


@dataclass_json
@dataclass
class MemberResponse:
    updated_at: datetime = field(metadata=config(field_name="updated_at"))
    user: UserResponse = field(metadata=config(field_name="user"))
    user_id: str = field(metadata=config(field_name="user_id"))
    created_at: datetime = field(metadata=config(field_name="created_at"))
    custom: Dict[str, object] = field(metadata=config(field_name="custom"))
    role: Optional[str] = field(metadata=config(field_name="role"), default=None)
    deleted_at: Optional[datetime] = field(
        metadata=config(field_name="deleted_at"), default=None
    )
