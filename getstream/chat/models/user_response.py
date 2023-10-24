# THIS FILE IS GENERATED FROM github.com/GetStream/protocol/tree/main/openapi-gen/templates/python/type.tmpl
from dataclasses import dataclass, field
from dataclasses_json import config, dataclass_json

from typing import List, Optional
from datetime import datetime
from dateutil.parser import parse
from marshmallow import fields
from getstream.chat.models.push_notification_settings import PushNotificationSettings


@dataclass_json
@dataclass
class UserResponse:
    online: bool = field(metadata=config(field_name="online"))
    role: str = field(metadata=config(field_name="role"))
    shadow_banned: bool = field(metadata=config(field_name="shadow_banned"))
    id: str = field(metadata=config(field_name="id"))
    banned: bool = field(metadata=config(field_name="banned"))
    deleted_at: Optional[datetime] = field(
        metadata=config(
            field_name="deleted_at",
            encoder=lambda d: d.isoformat() if d is not None else None,
            decoder=parse,
            mm_field=fields.DateTime(format="iso"),
        ),
        default=None,
    )
    language: Optional[str] = field(
        metadata=config(field_name="language"), default=None
    )
    last_active: Optional[datetime] = field(
        metadata=config(
            field_name="last_active",
            encoder=lambda d: d.isoformat() if d is not None else None,
            decoder=parse,
            mm_field=fields.DateTime(format="iso"),
        ),
        default=None,
    )
    ban_expires: Optional[datetime] = field(
        metadata=config(
            field_name="ban_expires",
            encoder=lambda d: d.isoformat() if d is not None else None,
            decoder=parse,
            mm_field=fields.DateTime(format="iso"),
        ),
        default=None,
    )
    push_notifications: Optional[PushNotificationSettings] = field(
        metadata=config(field_name="push_notifications"), default=None
    )
    updated_at: Optional[datetime] = field(
        metadata=config(
            field_name="updated_at",
            encoder=lambda d: d.isoformat() if d is not None else None,
            decoder=parse,
            mm_field=fields.DateTime(format="iso"),
        ),
        default=None,
    )
    created_at: Optional[datetime] = field(
        metadata=config(
            field_name="created_at",
            encoder=lambda d: d.isoformat() if d is not None else None,
            decoder=parse,
            mm_field=fields.DateTime(format="iso"),
        ),
        default=None,
    )
    deactivated_at: Optional[datetime] = field(
        metadata=config(
            field_name="deactivated_at",
            encoder=lambda d: d.isoformat() if d is not None else None,
            decoder=parse,
            mm_field=fields.DateTime(format="iso"),
        ),
        default=None,
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
    invisible: Optional[bool] = field(
        metadata=config(field_name="invisible"), default=None
    )
