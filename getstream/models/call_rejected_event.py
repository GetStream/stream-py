from dataclasses import dataclass, field
from dataclasses_json import config, dataclass_json

from datetime import datetime
from marshmallow import fields
from getstream.models.call_response import CallResponse
from getstream.models.user_response import UserResponse


@dataclass_json
@dataclass
class CallRejectedEvent:
    call: CallResponse = field(metadata=config(field_name="call"))
    call_cid: str = field(metadata=config(field_name="call_cid"))
    created_at: datetime = field(
        metadata=config(
            field_name="created_at",
            encoder=datetime.isoformat,
            decoder=datetime.fromisoformat,
            mm_field=fields.DateTime(format="iso"),
        )
    )
    type: str = field(metadata=config(field_name="type"))
    user: UserResponse = field(metadata=config(field_name="user"))
