from dataclasses import dataclass

from datetime import datetime

from models.model_call_ring_event import UserResponse


@dataclass
class CallParticipantResponse:
    joined_at: datetime
    role: str
    user: UserResponse
    user_session_id: str
