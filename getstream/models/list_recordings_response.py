from dataclasses import dataclass, field

from dataclasses_json import config, dataclass_json
from call_recording import CallRecording


@dataclass_json
@dataclass
class ListRecordingsResponse:
    duration: str = field(metadata=config(field_name="duration"))
    recordings: list[CallRecording] = field(metadata=config(field_name="recordings"))
