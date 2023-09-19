from dataclasses import dataclass, field
from dataclasses_json import config, dataclass_json

from datetime import datetime
from marshmallow import fields
from getstream.models.call_participant_response import CallParticipantResponse


@dataclass_json
@dataclass
class CallSessionParticipantJoinedEvent:
    created_at: datetime = field(
        metadata=config(
            field_name="created_at",
            encoder=datetime.isoformat,
            decoder=datetime.fromisoformat,
            mm_field=fields.DateTime(format="iso"),
        )
    )
    participant: CallParticipantResponse = field(
        metadata=config(field_name="participant")
    )
    session_id: str = field(metadata=config(field_name="session_id"))
    type: str = field(metadata=config(field_name="type"))
    call_cid: str = field(metadata=config(field_name="call_cid"))
