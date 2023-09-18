from dataclasses import dataclass, field
from dataclasses_json import config, dataclass_json

from typing import Optional


@dataclass_json
@dataclass
class RecordSettingsRequest:
    audio_only: Optional[bool] = field(
        metadata=config(field_name="audio_only"), default=None
    )
    mode: Optional[str] = field(metadata=config(field_name="mode"), default=None)
    quality: Optional[str] = field(metadata=config(field_name="quality"), default=None)
