from typing import Dict, Any
from dataclasses import dataclass


@dataclass
class SendEventRequest:
    custom: Dict[str, Any] = None

    @classmethod
    def from_dict(cls, data: dict) -> "SendEventRequest":
        return cls(**data)
