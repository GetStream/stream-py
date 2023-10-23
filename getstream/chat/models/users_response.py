# THIS FILE IS GENERATED FROM github.com/GetStream/protocol/tree/main/openapi-gen/templates/python/type.tmpl
from dataclasses import dataclass, field
from dataclasses_json import config, dataclass_json

from typing import List
from getstream.chat.models.user_response import UserResponse


@dataclass_json
@dataclass
class UsersResponse:
    duration: str = field(metadata=config(field_name="duration"))
    users: List[UserResponse] = field(metadata=config(field_name="users"))
