from dataclasses import dataclass, field
from typing import Optional
from dataclasses_json import config, dataclass_json
from call_participant_response import CallParticipantResponse


@dataclass_json
@dataclass
class CallSessionParticipantLeftEvent:
    call_cid: str = field(metadata=config(field_name="call_cid"))
    created_at: str = field(metadata=config(field_name="created_at"))
    participant: CallParticipantResponse = field(
        metadata=config(field_name="participant")
    )
    session_id: str = field(metadata=config(field_name="session_id"))
    type: str = field(metadata=config(field_name="type"))
