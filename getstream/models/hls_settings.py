from dataclasses import dataclass, field
from typing import Optional
from dataclasses_json import config, dataclass_json


@dataclass_json
@dataclass
class Hlssettings:
    auto_on: bool = field(metadata=config(field_name="auto_on"))
    enabled: bool = field(metadata=config(field_name="enabled"))
    quality_tracks: list[str] = field(metadata=config(field_name="quality_tracks"))
