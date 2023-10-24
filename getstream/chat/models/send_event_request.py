# THIS FILE IS GENERATED FROM github.com/GetStream/protocol/tree/main/openapi-gen/templates/python/type.tmpl
from dataclasses import dataclass, field
from dataclasses_json import config, dataclass_json

from getstream.chat.models.event_request import EventRequest


@dataclass_json
@dataclass
class SendEventRequest:
    event: EventRequest = field(metadata=config(field_name="event"))
