from dataclasses import dataclass
from typing import Optional, List

from .model_call_state_response_fields import CallStateResponseFields


@dataclass
class QueryCallsResponse:
    calls: List[CallStateResponseFields]
    duration: str
    next: Optional[str] = None
    prev: Optional[str] = None

    @classmethod
    def from_dict(cls, data: dict) -> "QueryCallsResponse":
        data["calls"] = [CallStateResponseFields.from_dict(d) for d in data["calls"]]
        return cls(**data)
