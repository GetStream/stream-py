from dataclasses import dataclass
from typing import Optional


@dataclass
class BackstageSettingsRequest:
    enabled: Optional[bool] = None

    @classmethod
    def from_dict(cls, data: dict) -> "BackstageSettingsRequest":
        return cls(**data)
