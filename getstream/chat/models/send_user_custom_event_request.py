# THIS FILE IS GENERATED FROM github.com/GetStream/protocol/tree/main/openapi-gen/templates/python/type.tmpl
from dataclasses import dataclass, field
from dataclasses_json import config, dataclass_json

from getstream.chat.models.user_custom_event_request import UserCustomEventRequest


@dataclass_json
@dataclass
class SendUserCustomEventRequest:
    event: UserCustomEventRequest = field(metadata=config(field_name="event"))
