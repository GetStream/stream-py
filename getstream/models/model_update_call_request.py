from dataclasses import dataclass
from typing import Optional, Dict, Any
from datetime import datetime

from .model_call_settings_request import CallSettingsRequest


@dataclass
class UpdateCallRequest:
    custom: Optional[Dict[str, Any]]
    settings_override: Optional[CallSettingsRequest]
    starts_at: Optional[datetime]
