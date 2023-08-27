from dataclasses import dataclass
from typing import List


@dataclass
class HLSSettings:
    auto_on: bool
    enabled: bool
    quality_tracks: List[str]

    @classmethod
    def from_dict(cls, data: dict) -> "HLSSettings":
        return cls(**data)
