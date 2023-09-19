from dataclasses import dataclass, field
from dataclasses_json import config, dataclass_json

from typing import List


@dataclass_json
@dataclass
class Hlssettings:
    enabled: bool = field(metadata=config(field_name="enabled"))
    quality_tracks: List[str] = field(metadata=config(field_name="quality_tracks"))
    auto_on: bool = field(metadata=config(field_name="auto_on"))
