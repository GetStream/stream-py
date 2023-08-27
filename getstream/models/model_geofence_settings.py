from typing import List
from dataclasses import dataclass


@dataclass
class GeofenceSettings:
    names: List[str]

    @classmethod
    def from_dict(cls, data: dict) -> "GeofenceSettings":
        return cls(**data)
