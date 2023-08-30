from dataclasses import dataclass
from typing import Optional

from .model_call_request import CallRequest


@dataclass
class GetOrCreateCallRequest:
    data: Optional[CallRequest] = None
    members_limit: Optional[int] = None
    notify: Optional[bool] = None
    ring: Optional[bool] = None

    @classmethod
    def from_dict(cls, data: dict) -> "GetOrCreateCallRequest":
        if data.get("data"):
            data["data"] = CallRequest.from_dict(data["data"])
        return cls(**data)
