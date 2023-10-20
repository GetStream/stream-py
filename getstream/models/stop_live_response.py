# THIS FILE IS GENERATED FROM github.com/GetStream/protocol/tree/main/openapi-gen/templates/python/type.tmpl
from dataclasses import dataclass, field
from dataclasses_json import config, dataclass_json

from getstream.models.call_response import CallResponse


@dataclass_json
@dataclass
class StopLiveResponse:
    call: CallResponse = field(metadata=config(field_name="call"))
    duration: str = field(metadata=config(field_name="duration"))
