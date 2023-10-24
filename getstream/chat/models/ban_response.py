# THIS FILE IS GENERATED FROM github.com/GetStream/protocol/tree/main/openapi-gen/templates/python/type.tmpl
from dataclasses import dataclass, field
from dataclasses_json import config, dataclass_json

from typing import Optional
from datetime import datetime
from dateutil.parser import parse
from marshmallow import fields
from getstream.chat.models.channel_response import ChannelResponse
from getstream.chat.models.user_object import UserObject


@dataclass_json
@dataclass
class BanResponse:
    created_at: Optional[datetime] = field(
        metadata=config(
            field_name="created_at",
            encoder=lambda d: d.isoformat(),
            decoder=parse,
            mm_field=fields.DateTime(format="iso"),
        ),
        default=None,
    )
    user: Optional[UserObject] = field(metadata=config(field_name="user"), default=None)
    banned_by: Optional[UserObject] = field(
        metadata=config(field_name="banned_by"), default=None
    )
    channel: Optional[ChannelResponse] = field(
        metadata=config(field_name="channel"), default=None
    )
    expires: Optional[datetime] = field(
        metadata=config(
            field_name="expires",
            encoder=lambda d: d.isoformat() if d is not None else None,
            decoder=parse,
            mm_field=fields.DateTime(format="iso"),
        ),
        default=None,
    )
    reason: Optional[str] = field(metadata=config(field_name="reason"), default=None)
    shadow: Optional[bool] = field(metadata=config(field_name="shadow"), default=None)
