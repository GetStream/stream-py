from dataclasses import dataclass
from typing import List, Dict
from datetime import datetime

from models.model_call_member_removed_event import CallResponse


@dataclass
class CallUpdatedEvent:
    Call: CallResponse
    CallCid: str
    CapabilitiesByRole: Dict[str, List[str]]
    CreatedAt: datetime
    Type: str
