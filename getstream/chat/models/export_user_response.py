# THIS FILE IS GENERATED FROM github.com/GetStream/protocol/tree/main/openapi-gen/templates/python/type.tmpl
from dataclasses import dataclass, field
from dataclasses_json import config, dataclass_json

from typing import List, Optional
from getstream.chat.models.user_object import UserObject
from getstream.chat.models.message import Message
from getstream.chat.models.reaction import Reaction


@dataclass_json
@dataclass
class ExportUserResponse:
    duration: str = field(metadata=config(field_name="duration"))
    user: Optional[UserObject] = field(metadata=config(field_name="user"), default=None)
    messages: Optional[List[Message]] = field(
        metadata=config(field_name="messages"), default=None
    )
    reactions: Optional[List[Reaction]] = field(
        metadata=config(field_name="reactions"), default=None
    )
