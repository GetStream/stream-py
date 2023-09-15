from dataclasses import dataclass, field

from dataclasses_json import config, dataclass_json


@dataclass_json
@dataclass
class CallRecording:
    url: str = field(metadata=config(field_name="url"))
    end_time: str = field(metadata=config(field_name="end_time"))
    filename: str = field(metadata=config(field_name="filename"))
    start_time: str = field(metadata=config(field_name="start_time"))
