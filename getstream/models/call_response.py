from dataclasses import dataclass, field
from dataclasses_json import config, dataclass_json

from typing import List, Dict, Optional
from datetime import datetime
from dateutil.parser import parse
from marshmallow import fields
from getstream.models.user_response import UserResponse
from getstream.models.call_settings_response import CallSettingsResponse
from getstream.models.call_ingress_response import CallIngressResponse
from getstream.models.egress_response import EgressResponse
from getstream.models.call_session_response import CallSessionResponse


@dataclass_json
@dataclass
class CallResponse:
    ingress: CallIngressResponse = field(metadata=config(field_name="ingress"))
    backstage: bool = field(metadata=config(field_name="backstage"))
    egress: EgressResponse = field(metadata=config(field_name="egress"))
    blocked_user_ids: List[str] = field(metadata=config(field_name="blocked_user_ids"))
    custom: Dict[str, object] = field(metadata=config(field_name="custom"))
    recording: bool = field(metadata=config(field_name="recording"))
    type: str = field(metadata=config(field_name="type"))
    cid: str = field(metadata=config(field_name="cid"))
    created_at: datetime = field(
        metadata=config(
            field_name="created_at",
            encoder=lambda d: d.isoformat(),
            decoder=parse,
            mm_field=fields.DateTime(format="iso"),
        )
    )
    created_by: UserResponse = field(metadata=config(field_name="created_by"))
    current_session_id: str = field(metadata=config(field_name="current_session_id"))
    id: str = field(metadata=config(field_name="id"))
    settings: CallSettingsResponse = field(metadata=config(field_name="settings"))
    transcribing: bool = field(metadata=config(field_name="transcribing"))
    updated_at: datetime = field(
        metadata=config(
            field_name="updated_at",
            encoder=lambda d: d.isoformat(),
            decoder=parse,
            mm_field=fields.DateTime(format="iso"),
        )
    )
    team: Optional[str] = field(metadata=config(field_name="team"), default=None)
    ended_at: Optional[datetime] = field(
        metadata=config(
            field_name="ended_at",
            encoder=lambda d: d.isoformat(),
            decoder=parse,
            mm_field=fields.DateTime(format="iso"),
        ),
        default=None,
    )
    session: Optional[CallSessionResponse] = field(
        metadata=config(field_name="session"), default=None
    )
    starts_at: Optional[datetime] = field(
        metadata=config(
            field_name="starts_at",
            encoder=lambda d: d.isoformat(),
            decoder=parse,
            mm_field=fields.DateTime(format="iso"),
        ),
        default=None,
    )
