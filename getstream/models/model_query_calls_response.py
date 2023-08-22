from dataclasses import dataclass
from typing import Optional, List

from models.model_call_state_response_fields import CallStateResponseFields


@dataclass
class QueryCallsResponse:
    calls: List[CallStateResponseFields]
    duration: str
    next: Optional[str] = None
    prev: Optional[str] = None
