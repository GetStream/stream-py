from dataclasses import dataclass, field
from dataclasses_json import config, dataclass_json

from typing import List, Dict
from datetime import datetime
from marshmallow import fields
from getstream.models.member_response import MemberResponse
from getstream.models.call_response import CallResponse


@dataclass_json
@dataclass
class CallMemberUpdatedPermissionEvent:
    capabilities_by_role: Dict[str, List[str]] = field(
        metadata=config(field_name="capabilities_by_role")
    )
    created_at: datetime = field(
        metadata=config(
            field_name="created_at",
            encoder=datetime.isoformat,
            decoder=datetime.fromisoformat,
            mm_field=fields.DateTime(format="iso"),
        )
    )
    members: List[MemberResponse] = field(metadata=config(field_name="members"))
    type: str = field(metadata=config(field_name="type"))
    call: CallResponse = field(metadata=config(field_name="call"))
    call_cid: str = field(metadata=config(field_name="call_cid"))
