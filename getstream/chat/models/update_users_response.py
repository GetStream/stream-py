from dataclasses import dataclass, field
from typing import Dict

from dataclasses_json import config, dataclass_json

from getstream.chat.models.user_object import UserObject


@dataclass_json
@dataclass
class UpdateUsersResponse:
    duration: str = field(metadata=config(field_name="duration"))
    users: Dict[str, UserObject] = field(metadata=config(field_name="users"))
