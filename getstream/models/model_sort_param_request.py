from dataclasses import dataclass
from typing import Optional


@dataclass
class SortParamRequest:
    direction: Optional[int]
    field: Optional[str]

    @classmethod
    def from_dict(cls, data: dict) -> "SortParamRequest":
        return cls(**data)
