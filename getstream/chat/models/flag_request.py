# THIS FILE IS GENERATED FROM github.com/GetStream/protocol/tree/main/openapi-gen/templates/python/type.tmpl
from dataclasses import dataclass, field
from dataclasses_json import config, dataclass_json

from typing import Optional
from getstream.chat.models.user_object_request import UserObjectRequest


@dataclass_json
@dataclass
class FlagRequest:
    target_message_id: Optional[str] = field(
        metadata=config(field_name="target_message_id"), default=None
    )
    target_user_id: Optional[str] = field(
        metadata=config(field_name="target_user_id"), default=None
    )
    user: Optional[UserObjectRequest] = field(
        metadata=config(field_name="user"), default=None
    )
    user_id: Optional[str] = field(metadata=config(field_name="user_id"), default=None)
