from typing import Dict, Any
from dataclasses import dataclass


@dataclass
class SendEventRequest:
    custom: Dict[str, Any] = None
