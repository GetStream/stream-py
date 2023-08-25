from dataclasses import dataclass

from datetime import datetime

from .model_user_response import UserResponse


@dataclass
class CallParticipantResponse:

    joined_at: datetime
    role: str
    user: UserResponse
    user_session_id: str
