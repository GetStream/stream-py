# THIS FILE IS GENERATED FROM github.com/GetStream/protocol/tree/main/openapi-gen/templates/python/type.tmpl
from dataclasses import dataclass, field
from dataclasses_json import config, dataclass_json

from typing import List, Optional
from datetime import datetime
from dateutil.parser import parse
from marshmallow import fields
from getstream.models.egress_response import EgressResponse
from getstream.models.call_settings_response import CallSettingsResponse
from getstream.models.user_response import UserResponse
from getstream.models.call_ingress_response import CallIngressResponse
from getstream.models.call_session_response import CallSessionResponse
from getstream.models.thumbnail_response import ThumbnailResponse


@dataclass_json
@dataclass
class CallResponse:
    backstage: bool = field(metadata=config(field_name="backstage"))
    cid: str = field(metadata=config(field_name="cid"))
    current_session_id: str = field(metadata=config(field_name="current_session_id"))
    egress: EgressResponse = field(metadata=config(field_name="egress"))
    settings: CallSettingsResponse = field(metadata=config(field_name="settings"))
    transcribing: bool = field(metadata=config(field_name="transcribing"))
    created_at: datetime = field(
        metadata=config(
            field_name="created_at",
            encoder=lambda d: d.isoformat(),
            decoder=parse,
            mm_field=fields.DateTime(format="iso"),
        )
    )
    created_by: UserResponse = field(metadata=config(field_name="created_by"))
    type: str = field(metadata=config(field_name="type"))
    blocked_user_ids: List[str] = field(metadata=config(field_name="blocked_user_ids"))
    custom: object = field(metadata=config(field_name="custom"))
    id: str = field(metadata=config(field_name="id"))
    ingress: CallIngressResponse = field(metadata=config(field_name="ingress"))
    recording: bool = field(metadata=config(field_name="recording"))
    updated_at: datetime = field(
        metadata=config(
            field_name="updated_at",
            encoder=lambda d: d.isoformat(),
            decoder=parse,
            mm_field=fields.DateTime(format="iso"),
        )
    )
    ended_at: Optional[datetime] = field(
        metadata=config(
            field_name="ended_at",
            encoder=lambda d: d.isoformat() if d is not None else None,
            decoder=parse,
            mm_field=fields.DateTime(format="iso"),
        ),
        default=None,
    )
    starts_at: Optional[datetime] = field(
        metadata=config(
            field_name="starts_at",
            encoder=lambda d: d.isoformat() if d is not None else None,
            decoder=parse,
            mm_field=fields.DateTime(format="iso"),
        ),
        default=None,
    )
    thumbnails: Optional[ThumbnailResponse] = field(
        metadata=config(field_name="thumbnails"), default=None
    )
    session: Optional[CallSessionResponse] = field(
        metadata=config(field_name="session"), default=None
    )
    team: Optional[str] = field(metadata=config(field_name="team"), default=None)
