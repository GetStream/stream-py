from dataclasses import dataclass
from datetime import datetime
from typing import List

from .model_call_response import CallResponse


@dataclass
class CallMemberRemovedEvent:
    call: CallResponse
    call_cid: str
    created_at: datetime
    members: List[str]
    type: str

    @classmethod
    def from_dict(cls, data: dict) -> "CallMemberRemovedEvent":
        data["call"] = CallResponse.from_dict(data["call"])

        return cls(**data)
