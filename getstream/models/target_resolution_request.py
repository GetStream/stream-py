from dataclasses import dataclass, field
from dataclasses_json import config, dataclass_json

from typing import Optional


@dataclass_json
@dataclass
class TargetResolutionRequest:
    width: Optional[int] = field(metadata=config(field_name="width"), default=None)
    bitrate: Optional[int] = field(metadata=config(field_name="bitrate"), default=None)
    height: Optional[int] = field(metadata=config(field_name="height"), default=None)
