from dataclasses import dataclass
from typing import Optional


@dataclass
class BackstageSettingsRequest:
    enabled: Optional[bool] = None
