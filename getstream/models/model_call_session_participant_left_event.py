from dataclasses import dataclass
from datetime import datetime

from .model_call_participant_response import CallParticipantResponse


@dataclass
class CallSessionParticipantLeftEvent:
    CallCid: str
    CreatedAt: datetime
    Participant: CallParticipantResponse
    SessionId: str
    Type: str
