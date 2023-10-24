# THIS FILE IS GENERATED FROM github.com/GetStream/protocol/tree/main/openapi-gen/templates/python/type.tmpl
from dataclasses import dataclass, field
from dataclasses_json import config, dataclass_json

from typing import List, Optional
from datetime import datetime
from dateutil.parser import parse
from marshmallow import fields
from getstream.chat.models.push_notification_settings_request import (
    PushNotificationSettingsRequest,
)


@dataclass_json
@dataclass
class UserObjectRequest:
    id: str = field(metadata=config(field_name="id"))
    ban_expires: Optional[datetime] = field(
        metadata=config(
            field_name="ban_expires",
            encoder=lambda d: d.isoformat() if d is not None else None,
            decoder=parse,
            mm_field=fields.DateTime(format="iso"),
        ),
        default=None,
    )
    invisible: Optional[bool] = field(
        metadata=config(field_name="invisible"), default=None
    )
    push_notifications: Optional[PushNotificationSettingsRequest] = field(
        metadata=config(field_name="push_notifications"), default=None
    )
    role: Optional[str] = field(metadata=config(field_name="role"), default=None)
    banned: Optional[bool] = field(metadata=config(field_name="banned"), default=None)
    language: Optional[str] = field(
        metadata=config(field_name="language"), default=None
    )
    revoke_tokens_issued_before: Optional[datetime] = field(
        metadata=config(
            field_name="revoke_tokens_issued_before",
            encoder=lambda d: d.isoformat() if d is not None else None,
            decoder=parse,
            mm_field=fields.DateTime(format="iso"),
        ),
        default=None,
    )
    teams: Optional[List[str]] = field(
        metadata=config(field_name="teams"), default=None
    )
