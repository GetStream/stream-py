from dataclasses import dataclass, field
from typing import Optional
from dataclasses_json import config, dataclass_json


@dataclass_json
@dataclass
class StopRecordingResponse:
    duration: str = field(metadata=config(field_name="duration"))
