from dataclasses import dataclass
from typing import List


@dataclass
class HLSSettings:
    auto_on: bool
    enabled: bool
    quality_tracks: List[str]
