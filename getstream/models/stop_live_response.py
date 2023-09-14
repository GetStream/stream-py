from dataclasses import dataclass, field
from typing import Optional
from dataclasses_json import config, dataclass_json
from call_response import CallResponse


@dataclass_json
@dataclass
class StopLiveResponse:
    duration: str = field(metadata=config(field_name="duration"))
    call: CallResponse = field(metadata=config(field_name="call"))
