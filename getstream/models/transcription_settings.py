from dataclasses import dataclass, field

from dataclasses_json import config, dataclass_json


@dataclass_json
@dataclass
class TranscriptionSettings:
    closed_caption_mode: str = field(metadata=config(field_name="closed_caption_mode"))
    mode: str = field(metadata=config(field_name="mode"))
