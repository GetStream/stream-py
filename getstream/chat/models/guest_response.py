# THIS FILE IS GENERATED FROM github.com/GetStream/protocol/tree/main/openapi-gen/templates/python/type.tmpl
from dataclasses import dataclass, field
from dataclasses_json import config, dataclass_json

from typing import Optional
from getstream.chat.models.user_object import UserObject


@dataclass_json
@dataclass
class GuestResponse:
    access_token: str = field(metadata=config(field_name="access_token"))
    duration: str = field(metadata=config(field_name="duration"))
    user: Optional[UserObject] = field(metadata=config(field_name="user"), default=None)
