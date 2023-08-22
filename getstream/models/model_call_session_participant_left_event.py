from dataclasses import dataclass
from typing import Any
from datetime import datetime

from models.model_call_participant_response import CallParticipantResponse


@dataclass
class CallSessionParticipantLeftEvent:
    CallCid: str
    CreatedAt: datetime
    Participant: CallParticipantResponse
    SessionId: str
    Type: str
