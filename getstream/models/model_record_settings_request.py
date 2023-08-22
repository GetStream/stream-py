from dataclasses import dataclass
from typing import Optional


@dataclass
class RecordSettingsRequest:
    audio_only: Optional[bool] = None
    mode: Optional[str] = None
    quality: Optional[str] = None
