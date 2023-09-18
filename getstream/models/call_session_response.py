from dataclasses import dataclass, field
from dataclasses_json import config, dataclass_json

from typing import Dict, List, Optional
from datetime import datetime
from getstream.models.call_participant_response import CallParticipantResponse


@dataclass_json
@dataclass
class CallSessionResponse:
    accepted_by: Dict[str, datetime] = field(metadata=config(field_name="accepted_by"))
    id: str = field(metadata=config(field_name="id"))
    participants: List[CallParticipantResponse] = field(
        metadata=config(field_name="participants")
    )
    participants_count_by_role: Dict[str, int] = field(
        metadata=config(field_name="participants_count_by_role")
    )
    rejected_by: Dict[str, datetime] = field(metadata=config(field_name="rejected_by"))
    ended_at: Optional[datetime] = field(
        metadata=config(field_name="ended_at"), default=None
    )
    live_started_at: Optional[datetime] = field(
        metadata=config(field_name="live_started_at"), default=None
    )
    live_ended_at: Optional[datetime] = field(
        metadata=config(field_name="live_ended_at"), default=None
    )
    started_at: Optional[datetime] = field(
        metadata=config(field_name="started_at"), default=None
    )
