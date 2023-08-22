from dataclasses import dataclass
from typing import Optional


@dataclass
class AudioSettingsRequest:
    access_request_enabled: Optional[bool] = None
    default_device: str = ""
    mic_default_on: Optional[bool] = None
    opus_dtx_enabled: Optional[bool] = None
    redundant_coding_enabled: Optional[bool] = None
    speaker_default_on: Optional[bool] = None
