from dataclasses import dataclass, field
from dataclasses_json import config, dataclass_json

from typing import List
from getstream.models.call_recording import CallRecording


@dataclass_json
@dataclass
class ListRecordingsResponse:
    recordings: List[CallRecording] = field(metadata=config(field_name="recordings"))
    duration: str = field(metadata=config(field_name="duration"))
