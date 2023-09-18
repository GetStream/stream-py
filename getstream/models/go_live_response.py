from dataclasses import dataclass, field
from dataclasses_json import config, dataclass_json

from getstream.models.call_response import CallResponse


@dataclass_json
@dataclass
class GoLiveResponse:
    duration: str = field(metadata=config(field_name="duration"))
    call: CallResponse = field(metadata=config(field_name="call"))
