from dataclasses import dataclass

from models.model_target_resolution import TargetResolution


@dataclass
class VideoSettings:
    access_request_enabled: bool
    camera_default_on: bool
    camera_facing: str
    enabled: bool
    target_resolution: TargetResolution
