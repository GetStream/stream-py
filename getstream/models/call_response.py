from dataclasses import dataclass, field
from dataclasses_json import config, dataclass_json

from typing import List, Dict, Optional
from datetime import datetime
from marshmallow import fields
from getstream.models.egress_response import EgressResponse
from getstream.models.call_ingress_response import CallIngressResponse
from getstream.models.call_session_response import CallSessionResponse
from getstream.models.user_response import UserResponse
from getstream.models.call_settings_response import CallSettingsResponse


@dataclass_json
@dataclass
class CallResponse:
    backstage: bool = field(metadata=config(field_name="backstage"))
    cid: str = field(metadata=config(field_name="cid"))
    type: str = field(metadata=config(field_name="type"))
    custom: Dict[str, object] = field(metadata=config(field_name="custom"))
    ingress: CallIngressResponse = field(metadata=config(field_name="ingress"))
    blocked_user_ids: List[str] = field(metadata=config(field_name="blocked_user_ids"))
    created_at: datetime = field(
        metadata=config(
            field_name="created_at",
            encoder=datetime.isoformat,
            decoder=datetime.fromisoformat,
            mm_field=fields.DateTime(format="iso"),
        )
    )
    created_by: UserResponse = field(metadata=config(field_name="created_by"))
    current_session_id: str = field(metadata=config(field_name="current_session_id"))
    recording: bool = field(metadata=config(field_name="recording"))
    settings: CallSettingsResponse = field(metadata=config(field_name="settings"))
    egress: EgressResponse = field(metadata=config(field_name="egress"))
    id: str = field(metadata=config(field_name="id"))
    transcribing: bool = field(metadata=config(field_name="transcribing"))
    updated_at: datetime = field(
        metadata=config(
            field_name="updated_at",
            encoder=datetime.isoformat,
            decoder=datetime.fromisoformat,
            mm_field=fields.DateTime(format="iso"),
        )
    )
    starts_at: Optional[datetime] = field(
        metadata=config(
            field_name="starts_at",
            encoder=datetime.isoformat,
            decoder=datetime.fromisoformat,
            mm_field=fields.DateTime(format="iso"),
        ),
        default=None,
    )
    ended_at: Optional[datetime] = field(
        metadata=config(
            field_name="ended_at",
            encoder=datetime.isoformat,
            decoder=datetime.fromisoformat,
            mm_field=fields.DateTime(format="iso"),
        ),
        default=None,
    )
    session: Optional[CallSessionResponse] = field(
        metadata=config(field_name="session"), default=None
    )
    team: Optional[str] = field(metadata=config(field_name="team"), default=None)
