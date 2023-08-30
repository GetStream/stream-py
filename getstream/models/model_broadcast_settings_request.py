from dataclasses import dataclass
from typing import Optional

from .model_hls_settings_request import HLSSettingsRequest


@dataclass
class BroadcastSettingsRequest:
    enabled: Optional[bool] = None
    hls: Optional[HLSSettingsRequest] = None

    @classmethod
    def from_dict(cls, data: dict) -> "BroadcastSettingsRequest":
        return cls(**data)
