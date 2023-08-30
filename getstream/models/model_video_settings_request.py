from dataclasses import dataclass
from typing import Optional

from .model_target_resolution_request import TargetResolutionRequest


@dataclass
class VideoSettingsRequest:
    access_request_enabled: Optional[bool] = None
    camera_default_on: Optional[bool] = None
    camera_facing: Optional[str] = None
    enabled: Optional[bool] = None
    target_resolution: Optional[TargetResolutionRequest] = None

    @classmethod
    def from_dict(cls, data: dict) -> "VideoSettingsRequest":
        data["target_resolution"] = (
            TargetResolutionRequest.from_dict(data["target_resolution"])
            if data.get("target_resolution")
            else None
        )
        return cls(**data)
