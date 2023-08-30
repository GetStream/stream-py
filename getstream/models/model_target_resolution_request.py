from dataclasses import dataclass
from typing import Optional


@dataclass
class TargetResolutionRequest:
    bitrate: Optional[int] = None
    height: Optional[int] = None
    width: Optional[int] = None

    @classmethod
    def from_dict(cls, data: dict) -> "TargetResolutionRequest":
        return cls(**data)
