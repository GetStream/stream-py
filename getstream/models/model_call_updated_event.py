from dataclasses import dataclass
from typing import List, Dict
from datetime import datetime

from .model_call_member_removed_event from .model_call_response import CallResponse


@dataclass
class CallUpdatedEvent:
    Call: CallResponse
    CallCid: str
    CapabilitiesByRole: Dict[str, List[str]]
    CreatedAt: datetime
    Type: str
