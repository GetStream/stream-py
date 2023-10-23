# THIS FILE IS GENERATED FROM github.com/GetStream/protocol/tree/main/openapi-gen/templates/python/type.tmpl
from dataclasses import dataclass, field
from dataclasses_json import config, dataclass_json

from typing import List
from getstream.chat.models.message_flag import MessageFlag


@dataclass_json
@dataclass
class QueryMessageFlagsResponse:
    duration: str = field(metadata=config(field_name="duration"))
    flags: List[MessageFlag] = field(metadata=config(field_name="flags"))
