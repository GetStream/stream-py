from dataclasses import dataclass, field

from dataclasses_json import config, dataclass_json


@dataclass_json
@dataclass
class CallRecordingStoppedEvent:
    call_cid: str = field(metadata=config(field_name="call_cid"))
    created_at: str = field(metadata=config(field_name="created_at"))
    type: str = field(metadata=config(field_name="type"))
