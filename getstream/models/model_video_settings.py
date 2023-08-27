from dataclasses import dataclass

from .model_target_resolution import TargetResolution


@dataclass
class VideoSettings:
    access_request_enabled: bool
    camera_default_on: bool
    camera_facing: str
    enabled: bool
    target_resolution: TargetResolution

    @classmethod
    def from_dict(cls, data: dict) -> "VideoSettings":
        data["target_resolution"] = TargetResolution.from_dict(
            data["target_resolution"]
        )
        return cls(**data)
