from dataclasses import dataclass
from typing import List

from .model_edge_response import EdgeResponse


@dataclass
class GetEdgesResponse:
    duration: str
    edges: List[EdgeResponse]

    @classmethod
    def from_dict(cls, data: dict) -> "GetEdgesResponse":
        data["edges"] = [EdgeResponse.from_dict(d) for d in data["edges"]]
        return cls(**data)
