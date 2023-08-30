from dataclasses import dataclass
from typing import List, Dict
from datetime import datetime

from .model_call_response import CallResponse


@dataclass
class CallUpdatedEvent:
    call: CallResponse
    call_cid: str
    capabilities_by_role: Dict[str, List[str]]
    created_at: datetime
    type: str

    @classmethod
    def from_dict(cls, data: dict) -> "CallUpdatedEvent":
        data["call"] = CallResponse.from_dict(data["call"])

        return cls(**data)
