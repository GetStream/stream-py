# THIS FILE IS GENERATED FROM github.com/GetStream/protocol/tree/main/openapi-gen/templates/python/type.tmpl
from dataclasses import dataclass, field
from dataclasses_json import config, dataclass_json

from typing import Optional
from datetime import datetime
from dateutil.parser import parse
from marshmallow import fields
from getstream.chat.models.user_object import UserObject


@dataclass_json
@dataclass
class Read:
    unread_messages: int = field(metadata=config(field_name="unread_messages"))
    last_read: datetime = field(
        metadata=config(
            field_name="last_read",
            encoder=lambda d: d.isoformat(),
            decoder=parse,
            mm_field=fields.DateTime(format="iso"),
        )
    )
    last_read_message_id: Optional[str] = field(
        metadata=config(field_name="last_read_message_id"), default=None
    )
    user: Optional[UserObject] = field(metadata=config(field_name="user"), default=None)
