from dataclasses import dataclass, field

from dataclasses_json import config, dataclass_json


@dataclass_json
@dataclass
class TranscriptionSettingsRequest:
    closed_caption_mode: Optional[str] = field(
        metadata=config(field_name="closed_caption_mode"), default=None
    )
    mode: Optional[str] = field(metadata=config(field_name="mode"), default=None)
