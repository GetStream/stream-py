from dataclasses import dataclass, field
from dataclasses_json import config, dataclass_json


@dataclass_json
@dataclass
class TargetResolution:
    bitrate: int = field(metadata=config(field_name="bitrate"))
    height: int = field(metadata=config(field_name="height"))
    width: int = field(metadata=config(field_name="width"))
