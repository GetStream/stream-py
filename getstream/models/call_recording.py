from dataclasses import dataclass, field
from dataclasses_json import config, dataclass_json

from datetime import datetime


@dataclass_json
@dataclass
class CallRecording:
    end_time: datetime = field(metadata=config(field_name="end_time"))
    filename: str = field(metadata=config(field_name="filename"))
    start_time: datetime = field(metadata=config(field_name="start_time"))
    url: str = field(metadata=config(field_name="url"))
