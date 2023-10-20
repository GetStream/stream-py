# THIS FILE IS GENERATED FROM github.com/GetStream/protocol/tree/main/openapi-gen/templates/python/type.tmpl
from dataclasses import dataclass, field
from dataclasses_json import config, dataclass_json

from typing import List, Dict, Optional
from datetime import datetime
from dateutil.parser import parse
from marshmallow import fields
from getstream.models.thumbnail_response import ThumbnailResponse
from getstream.models.egress_response import EgressResponse
from getstream.models.call_settings_response import CallSettingsResponse
from getstream.models.user_response import UserResponse
from getstream.models.call_ingress_response import CallIngressResponse
from getstream.models.call_session_response import CallSessionResponse


@dataclass_json
@dataclass
class CallResponse:
    egress: EgressResponse = field(metadata=config(field_name="egress"))
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
    blocked_user_ids: List[str] = field(metadata=config(field_name="blocked_user_ids"))
    created_at: datetime = field(
        metadata=config(
            field_name="created_at",
            encoder=lambda d: d.isoformat(),
            decoder=parse,
            mm_field=fields.DateTime(format="iso"),
        )
    )
    custom: Dict[str, object] = field(metadata=config(field_name="custom"))
    ingress: CallIngressResponse = field(metadata=config(field_name="ingress"))
    cid: str = field(metadata=config(field_name="cid"))
    created_by: UserResponse = field(metadata=config(field_name="created_by"))
    id: str = field(metadata=config(field_name="id"))
    type: str = field(metadata=config(field_name="type"))
    backstage: bool = field(metadata=config(field_name="backstage"))
    current_session_id: str = field(metadata=config(field_name="current_session_id"))
    recording: bool = field(metadata=config(field_name="recording"))
    starts_at: Optional[datetime] = field(
        metadata=config(
            field_name="starts_at",
            encoder=lambda d: d.isoformat() if d is not None else None,
            decoder=parse,
            mm_field=fields.DateTime(format="iso"),
        ),
        default=None,
    )
    team: Optional[str] = field(metadata=config(field_name="team"), default=None)
    ended_at: Optional[datetime] = field(
        metadata=config(
            field_name="ended_at",
            encoder=lambda d: d.isoformat() if d is not None else None,
            decoder=parse,
            mm_field=fields.DateTime(format="iso"),
        ),
        default=None,
    )
    session: Optional[CallSessionResponse] = field(
        metadata=config(field_name="session"), default=None
    )
    thumbnails: Optional[ThumbnailResponse] = field(
        metadata=config(field_name="thumbnails"), default=None
    )
