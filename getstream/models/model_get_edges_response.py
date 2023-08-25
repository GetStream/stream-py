from dataclasses import dataclass
from typing import List

from .model_edge_response import EdgeResponse


@dataclass
class GetEdgesResponse:
    duration: str
    edges: List[EdgeResponse]
