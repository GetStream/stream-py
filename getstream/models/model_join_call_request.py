from dataclasses import dataclass
from typing import Optional

from .model_call_request import CallRequest


@dataclass
class JoinCallRequest:
    create: Optional[bool] = None
    data: Optional[CallRequest] = None
    location: str = ""
    members_limit: Optional[int] = None
    migrating_from: Optional[str] = None
    notify: Optional[bool] = None
    ring: Optional[bool] = None
