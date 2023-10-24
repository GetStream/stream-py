# THIS FILE IS GENERATED FROM github.com/GetStream/protocol/tree/main/openapi-gen/templates/python/type.tmpl
from dataclasses import dataclass, field
from dataclasses_json import config, dataclass_json

from typing import Optional
from getstream.chat.models.message_read_event import MessageReadEvent


@dataclass_json
@dataclass
class MarkReadResponse:
    duration: str = field(metadata=config(field_name="duration"))
    event: Optional[MessageReadEvent] = field(
        metadata=config(field_name="event"), default=None
    )
