# THIS FILE IS GENERATED FROM github.com/GetStream/protocol/tree/main/openapi-gen/templates/python/type.tmpl
from dataclasses import dataclass, field
from dataclasses_json import config, dataclass_json

from typing import Dict, List, Optional
from datetime import datetime
from dateutil.parser import parse
from marshmallow import fields
from getstream.models.call_participant_response import CallParticipantResponse


@dataclass_json
@dataclass
class CallSessionResponse:
    participants_count_by_role: Dict[str, int] = field(
        metadata=config(field_name="participants_count_by_role")
    )
    accepted_by: Dict[str, datetime] = field(metadata=config(field_name="accepted_by"))
    participants: List[CallParticipantResponse] = field(
        metadata=config(field_name="participants")
    )
    rejected_by: Dict[str, datetime] = field(metadata=config(field_name="rejected_by"))
    id: str = field(metadata=config(field_name="id"))
    ended_at: Optional[datetime] = field(
        metadata=config(
            field_name="ended_at",
            encoder=lambda d: d.isoformat() if d is not None else None,
            decoder=parse,
            mm_field=fields.DateTime(format="iso"),
        ),
        default=None,
    )
    live_ended_at: Optional[datetime] = field(
        metadata=config(
            field_name="live_ended_at",
            encoder=lambda d: d.isoformat() if d is not None else None,
            decoder=parse,
            mm_field=fields.DateTime(format="iso"),
        ),
        default=None,
    )
    live_started_at: Optional[datetime] = field(
        metadata=config(
            field_name="live_started_at",
            encoder=lambda d: d.isoformat() if d is not None else None,
            decoder=parse,
            mm_field=fields.DateTime(format="iso"),
        ),
        default=None,
    )
    started_at: Optional[datetime] = field(
        metadata=config(
            field_name="started_at",
            encoder=lambda d: d.isoformat() if d is not None else None,
            decoder=parse,
            mm_field=fields.DateTime(format="iso"),
        ),
        default=None,
    )
