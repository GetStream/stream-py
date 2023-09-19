from dataclasses import dataclass, field
from dataclasses_json import config, dataclass_json

from getstream.models.hls_settings import Hlssettings


@dataclass_json
@dataclass
class BroadcastSettings:
    enabled: bool = field(metadata=config(field_name="enabled"))
    hls: Hlssettings = field(metadata=config(field_name="hls"))
