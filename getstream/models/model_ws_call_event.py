from dataclasses import dataclass
from typing import Optional


@dataclass
class WSCallEvent:
    call_cid: Optional[str] = None

    @classmethod
    def from_dict(cls, data: dict) -> "WSCallEvent":
        return cls(**data)
