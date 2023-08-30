from dataclasses import dataclass
from typing import List


@dataclass
class RequestPermissionRequest:
    permissions: List[str]

    @classmethod
    def from_dict(cls, data: dict) -> "RequestPermissionRequest":
        return cls(**data)
