from dataclasses import dataclass, field

from dataclasses_json import config, dataclass_json
from call_participant_response import CallParticipantResponse


@dataclass_json
@dataclass
class CallSessionResponse:
    participants: list[CallParticipantResponse] = field(
        metadata=config(field_name="participants")
    )
    participants_count_by_role: dict[str, int] = field(
        metadata=config(field_name="participants_count_by_role")
    )
    id: str = field(metadata=config(field_name="id"))
    rejected_by: dict[str, str] = field(metadata=config(field_name="rejected_by"))
    accepted_by: dict[str, str] = field(metadata=config(field_name="accepted_by"))
    live_ended_at: Optional[str] = field(
        metadata=config(field_name="live_ended_at"), default=None
    )
    live_started_at: Optional[str] = field(
        metadata=config(field_name="live_started_at"), default=None
    )
    ended_at: Optional[str] = field(
        metadata=config(field_name="ended_at"), default=None
    )
    started_at: Optional[str] = field(
        metadata=config(field_name="started_at"), default=None
    )
