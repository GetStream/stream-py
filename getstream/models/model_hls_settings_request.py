from dataclasses import dataclass
from typing import List, Optional


@dataclass
class HLSSettingsRequest:
    auto_on: Optional[bool] = None
    enabled: Optional[bool] = None
    quality_tracks: List[str] = None
