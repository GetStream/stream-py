# THIS FILE IS GENERATED FROM github.com/GetStream/protocol/tree/main/openapi-gen/templates/python/type.tmpl
from dataclasses import dataclass, field
from dataclasses_json import config, dataclass_json

from typing import Optional
from datetime import datetime
from dateutil.parser import parse
from marshmallow import fields
from getstream.chat.models.user_object_request import UserObjectRequest
from getstream.chat.models.message_request import MessageRequest


@dataclass_json
@dataclass
class TruncateChannelRequest:
    hard_delete: Optional[bool] = field(
        metadata=config(field_name="hard_delete"), default=None
    )
    message: Optional[MessageRequest] = field(
        metadata=config(field_name="message"), default=None
    )
    skip_push: Optional[bool] = field(
        metadata=config(field_name="skip_push"), default=None
    )
    truncated_at: Optional[datetime] = field(
        metadata=config(
            field_name="truncated_at",
            encoder=lambda d: d.isoformat() if d is not None else None,
            decoder=parse,
            mm_field=fields.DateTime(format="iso"),
        ),
        default=None,
    )
    user: Optional[UserObjectRequest] = field(
        metadata=config(field_name="user"), default=None
    )
    user_id: Optional[str] = field(metadata=config(field_name="user_id"), default=None)
