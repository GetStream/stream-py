from dataclasses import dataclass
from datetime import datetime


@dataclass
class CallRecordingStoppedEvent:
    call_cid: str
    created_at: datetime
    type: str
