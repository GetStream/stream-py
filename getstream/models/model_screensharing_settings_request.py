from dataclasses import dataclass
from typing import Optional


@dataclass
class ScreensharingSettingsRequest:
    access_request_enabled: Optional[bool] = None
    enabled: Optional[bool] = None
