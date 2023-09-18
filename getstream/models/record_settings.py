from dataclasses import dataclass, field
from dataclasses_json import config, dataclass_json


@dataclass_json
@dataclass
class RecordSettings:
    quality: str = field(metadata=config(field_name="quality"))
    audio_only: bool = field(metadata=config(field_name="audio_only"))
    mode: str = field(metadata=config(field_name="mode"))
