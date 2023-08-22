from dataclasses import dataclass
from typing import Optional

from models.model_call_request import CallRequest


@dataclass
class GetOrCreateCallRequest:
    data: Optional[CallRequest] = None
    members_limit: Optional[int] = None
    notify: Optional[bool] = None
    ring: Optional[bool] = None
