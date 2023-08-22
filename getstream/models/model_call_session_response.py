from dataclasses import dataclass
from typing import Optional, List, Dict
from datetime import datetime

from models.model_call_participant_response import CallParticipantResponse


@dataclass
class CallSessionResponse:
    accepted_by: Dict[str, datetime]
    ended_at: Optional[datetime]
    id: str
    participants: List[CallParticipantResponse]
    participants_count_by_role: Dict[str, int]
    rejected_by: Dict[str, datetime]
    started_at: Optional[datetime]
