from dataclasses import dataclass, field
from typing import Optional
from dataclasses_json import config, dataclass_json


@dataclass_json
@dataclass
class TargetResolution:
    width: int = field(metadata=config(field_name="width"))
    bitrate: int = field(metadata=config(field_name="bitrate"))
    height: int = field(metadata=config(field_name="height"))
