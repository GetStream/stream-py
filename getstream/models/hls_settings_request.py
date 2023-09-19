from dataclasses import dataclass, field
from dataclasses_json import config, dataclass_json

from typing import List, Optional


@dataclass_json
@dataclass
class HlssettingsRequest:
    quality_tracks: Optional[List[str]] = field(
        metadata=config(field_name="quality_tracks"), default=None
    )
    auto_on: Optional[bool] = field(metadata=config(field_name="auto_on"), default=None)
    enabled: Optional[bool] = field(metadata=config(field_name="enabled"), default=None)
