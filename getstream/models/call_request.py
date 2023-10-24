# THIS FILE IS GENERATED FROM github.com/GetStream/protocol/tree/main/openapi-gen/templates/python/type.tmpl
from dataclasses import dataclass, field
from dataclasses_json import config, dataclass_json

from typing import Dict, List, Optional
from datetime import datetime
from dateutil.parser import parse
from marshmallow import fields
from getstream.models.call_settings_request import CallSettingsRequest
from getstream.models.user_request import UserRequest
from getstream.models.member_request import MemberRequest


@dataclass_json
@dataclass
class CallRequest:
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
    created_by: Optional[UserRequest] = field(
        metadata=config(field_name="created_by"), default=None
    )
    created_by_id: Optional[str] = field(
        metadata=config(field_name="created_by_id"), default=None
    )
    custom: Optional[Dict[str, object]] = field(
        metadata=config(field_name="custom"), default=None
    )
    members: Optional[List[MemberRequest]] = field(
        metadata=config(field_name="members"), default=None
    )
    settings_override: Optional[CallSettingsRequest] = field(
        metadata=config(field_name="settings_override"), default=None
    )
