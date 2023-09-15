from dataclasses import dataclass, field
from typing import Optional

from dataclasses_json import config, dataclass_json


@dataclass_json
@dataclass
class RecordSettingsRequest:
    quality: Optional[str] = field(metadata=config(field_name="quality"), default=None)
    audio_only: Optional[bool] = field(
        metadata=config(field_name="audio_only"), default=None
    )
    mode: Optional[str] = field(metadata=config(field_name="mode"), default=None)
