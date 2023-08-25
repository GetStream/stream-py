from dataclasses import dataclass
from datetime import datetime

from .model_call_participant_response import CallParticipantResponse


@dataclass
class CallSessionParticipantJoinedEvent:
    call_cid: str
    created_at: datetime
    participant: CallParticipantResponse
    session_id: str
    type: str
