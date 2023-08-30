from dataclasses import dataclass
from typing import Optional


@dataclass
class APNSRequest:
    body: Optional[str] = None
    title: Optional[str] = None

    @classmethod
    def from_dict(cls, data: dict) -> "APNSRequest":
        return cls(**data)
