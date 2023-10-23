# THIS FILE IS GENERATED FROM github.com/GetStream/protocol/tree/main/openapi-gen/templates/python/type.tmpl
from dataclasses import dataclass, field
from dataclasses_json import config, dataclass_json

from typing import Optional
from getstream.chat.models.user_object_request import UserObjectRequest


@dataclass_json
@dataclass
class ReactionRequest:
    type: str = field(metadata=config(field_name="type"))
    user: Optional[UserObjectRequest] = field(
        metadata=config(field_name="user"), default=None
    )
    user_id: Optional[str] = field(metadata=config(field_name="user_id"), default=None)
    message_id: Optional[str] = field(
        metadata=config(field_name="message_id"), default=None
    )
    score: Optional[int] = field(metadata=config(field_name="score"), default=None)
