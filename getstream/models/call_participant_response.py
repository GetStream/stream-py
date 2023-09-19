from dataclasses import dataclass, field
from dataclasses_json import config, dataclass_json

from datetime import datetime
from dateutil.parser import parse
from marshmallow import fields
from getstream.models.user_response import UserResponse


@dataclass_json
@dataclass
class CallParticipantResponse:
    role: str = field(metadata=config(field_name="role"))
    user: UserResponse = field(metadata=config(field_name="user"))
    user_session_id: str = field(metadata=config(field_name="user_session_id"))
    joined_at: datetime = field(
        metadata=config(
            field_name="joined_at",
            encoder=lambda d: d.isoformat(),
            decoder=parse,
            mm_field=fields.DateTime(format="iso"),
        )
    )
