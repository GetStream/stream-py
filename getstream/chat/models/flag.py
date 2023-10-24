# THIS FILE IS GENERATED FROM github.com/GetStream/protocol/tree/main/openapi-gen/templates/python/type.tmpl
from dataclasses import dataclass, field
from dataclasses_json import config, dataclass_json

from typing import Optional
from datetime import datetime
from dateutil.parser import parse
from marshmallow import fields
from getstream.chat.models.user_object import UserObject
from getstream.chat.models.flag_details import FlagDetails
from getstream.chat.models.message import Message


@dataclass_json
@dataclass
class Flag:
    created_by_automod: bool = field(metadata=config(field_name="created_by_automod"))
    updated_at: datetime = field(
        metadata=config(
            field_name="updated_at",
            encoder=lambda d: d.isoformat(),
            decoder=parse,
            mm_field=fields.DateTime(format="iso"),
        )
    )
    created_at: datetime = field(
        metadata=config(
            field_name="created_at",
            encoder=lambda d: d.isoformat(),
            decoder=parse,
            mm_field=fields.DateTime(format="iso"),
        )
    )
    details: Optional[FlagDetails] = field(
        metadata=config(field_name="details"), default=None
    )
    reviewed_at: Optional[datetime] = field(
        metadata=config(
            field_name="reviewed_at",
            encoder=lambda d: d.isoformat() if d is not None else None,
            decoder=parse,
            mm_field=fields.DateTime(format="iso"),
        ),
        default=None,
    )
    target_message: Optional[Message] = field(
        metadata=config(field_name="target_message"), default=None
    )
    target_message_id: Optional[str] = field(
        metadata=config(field_name="target_message_id"), default=None
    )
    approved_at: Optional[datetime] = field(
        metadata=config(
            field_name="approved_at",
            encoder=lambda d: d.isoformat() if d is not None else None,
            decoder=parse,
            mm_field=fields.DateTime(format="iso"),
        ),
        default=None,
    )
    rejected_at: Optional[datetime] = field(
        metadata=config(
            field_name="rejected_at",
            encoder=lambda d: d.isoformat() if d is not None else None,
            decoder=parse,
            mm_field=fields.DateTime(format="iso"),
        ),
        default=None,
    )
    target_user: Optional[UserObject] = field(
        metadata=config(field_name="target_user"), default=None
    )
    user: Optional[UserObject] = field(metadata=config(field_name="user"), default=None)
