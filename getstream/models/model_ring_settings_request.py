from dataclasses import dataclass
from typing import Optional


@dataclass
class RingSettingsRequest:
    auto_cancel_timeout_ms: Optional[int] = None
    incoming_call_timeout_ms: Optional[int] = None
