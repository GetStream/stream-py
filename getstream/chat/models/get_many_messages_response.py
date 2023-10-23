# THIS FILE IS GENERATED FROM github.com/GetStream/protocol/tree/main/openapi-gen/templates/python/type.tmpl
from dataclasses import dataclass, field
from dataclasses_json import config, dataclass_json

from typing import List
from getstream.chat.models.message import Message


@dataclass_json
@dataclass
class GetManyMessagesResponse:
    messages: List[Message] = field(metadata=config(field_name="messages"))
    duration: str = field(metadata=config(field_name="duration"))
