# THIS FILE IS GENERATED FROM github.com/GetStream/protocol/tree/main/openapi-gen/templates/python/type.tmpl
from dataclasses import dataclass, field
from dataclasses_json import config, dataclass_json

from typing import Optional
from datetime import datetime
from dateutil.parser import parse
from marshmallow import fields
from getstream.chat.models.user_object import UserObject
from getstream.chat.models.channel_response import ChannelResponse


@dataclass_json
@dataclass
class NotificationMarkUnreadEvent:
    unread_channels: int = field(metadata=config(field_name="unread_channels"))
    unread_messages: int = field(metadata=config(field_name="unread_messages"))
    last_read_at: datetime = field(
        metadata=config(
            field_name="last_read_at",
            encoder=lambda d: d.isoformat(),
            decoder=parse,
            mm_field=fields.DateTime(format="iso"),
        )
    )
    cid: str = field(metadata=config(field_name="cid"))
    total_unread_count: int = field(metadata=config(field_name="total_unread_count"))
    type: str = field(metadata=config(field_name="type"))
    channel_type: str = field(metadata=config(field_name="channel_type"))
    created_at: datetime = field(
        metadata=config(
            field_name="created_at",
            encoder=lambda d: d.isoformat(),
            decoder=parse,
            mm_field=fields.DateTime(format="iso"),
        )
    )
    first_unread_message_id: str = field(
        metadata=config(field_name="first_unread_message_id")
    )
    unread_count: int = field(metadata=config(field_name="unread_count"))
    channel_id: str = field(metadata=config(field_name="channel_id"))
    team: Optional[str] = field(metadata=config(field_name="team"), default=None)
    channel: Optional[ChannelResponse] = field(
        metadata=config(field_name="channel"), default=None
    )
    last_read_message_id: Optional[str] = field(
        metadata=config(field_name="last_read_message_id"), default=None
    )
    user: Optional[UserObject] = field(metadata=config(field_name="user"), default=None)
