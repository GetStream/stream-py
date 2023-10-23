# THIS FILE IS GENERATED FROM github.com/GetStream/protocol/tree/main/openapi-gen/templates/python/type.tmpl
from dataclasses import dataclass, field
from dataclasses_json import config, dataclass_json

from typing import Optional
from datetime import datetime
from dateutil.parser import parse
from marshmallow import fields
from getstream.chat.models.user_object_request import UserObjectRequest


@dataclass_json
@dataclass
class ChannelMemberRequest:
    invited: Optional[bool] = field(metadata=config(field_name="invited"), default=None)
    created_at: Optional[datetime] = field(
        metadata=config(
            field_name="created_at",
            encoder=lambda d: d.isoformat() if d is not None else None,
            decoder=parse,
            mm_field=fields.DateTime(format="iso"),
        ),
        default=None,
    )
    invite_rejected_at: Optional[datetime] = field(
        metadata=config(
            field_name="invite_rejected_at",
            encoder=lambda d: d.isoformat() if d is not None else None,
            decoder=parse,
            mm_field=fields.DateTime(format="iso"),
        ),
        default=None,
    )
    is_moderator: Optional[bool] = field(
        metadata=config(field_name="is_moderator"), default=None
    )
    role: Optional[str] = field(metadata=config(field_name="role"), default=None)
    shadow_banned: Optional[bool] = field(
        metadata=config(field_name="shadow_banned"), default=None
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
    user_id: Optional[str] = field(metadata=config(field_name="user_id"), default=None)
    invite_accepted_at: Optional[datetime] = field(
        metadata=config(
            field_name="invite_accepted_at",
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
    banned: Optional[bool] = field(metadata=config(field_name="banned"), default=None)
    channel_role: Optional[str] = field(
        metadata=config(field_name="channel_role"), default=None
    )
    deleted_at: Optional[datetime] = field(
        metadata=config(
            field_name="deleted_at",
            encoder=lambda d: d.isoformat() if d is not None else None,
            decoder=parse,
            mm_field=fields.DateTime(format="iso"),
        ),
        default=None,
    )
    user: Optional[UserObjectRequest] = field(
        metadata=config(field_name="user"), default=None
    )
