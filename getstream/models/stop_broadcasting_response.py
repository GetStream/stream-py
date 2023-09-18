from dataclasses import dataclass, field

from dataclasses_json import config, dataclass_json


@dataclass_json
@dataclass
class StopBroadcastingResponse:
    duration: str = field(metadata=config(field_name="duration"))