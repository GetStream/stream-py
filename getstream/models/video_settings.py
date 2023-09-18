from dataclasses import dataclass, field
from dataclasses_json import config, dataclass_json

from getstream.models.target_resolution import TargetResolution


@dataclass_json
@dataclass
class VideoSettings:
    camera_facing: str = field(metadata=config(field_name="camera_facing"))
    enabled: bool = field(metadata=config(field_name="enabled"))
    target_resolution: TargetResolution = field(
        metadata=config(field_name="target_resolution")
    )
    access_request_enabled: bool = field(
        metadata=config(field_name="access_request_enabled")
    )
    camera_default_on: bool = field(metadata=config(field_name="camera_default_on"))
