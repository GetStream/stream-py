# THIS FILE IS GENERATED FROM github.com/GetStream/protocol/tree/main/openapi-gen/templates/python/type.tmpl
from dataclasses import dataclass, field
from dataclasses_json import config, dataclass_json

from typing import List, Optional
from datetime import datetime
from dateutil.parser import parse
from marshmallow import fields
from getstream.chat.models.channel_response import ChannelResponse
from getstream.chat.models.channel_member import ChannelMember
from getstream.chat.models.message import Message
from getstream.chat.models.user_object import UserObject
from getstream.chat.models.pending_message import PendingMessage
from getstream.chat.models.read import Read


@dataclass_json
@dataclass
class ChannelStateResponseFields:
    pinned_messages: List[Message] = field(
        metadata=config(field_name="pinned_messages")
    )
    members: List[ChannelMember] = field(metadata=config(field_name="members"))
    messages: List[Message] = field(metadata=config(field_name="messages"))
    hidden: Optional[bool] = field(metadata=config(field_name="hidden"), default=None)
    hide_messages_before: Optional[datetime] = field(
        metadata=config(
            field_name="hide_messages_before",
            encoder=lambda d: d.isoformat() if d is not None else None,
            decoder=parse,
            mm_field=fields.DateTime(format="iso"),
        ),
        default=None,
    )
    pending_messages: Optional[List[PendingMessage]] = field(
        metadata=config(field_name="pending_messages"), default=None
    )
    read: Optional[List[Read]] = field(metadata=config(field_name="read"), default=None)
    watcher_count: Optional[int] = field(
        metadata=config(field_name="watcher_count"), default=None
    )
    channel: Optional[ChannelResponse] = field(
        metadata=config(field_name="channel"), default=None
    )
    membership: Optional[ChannelMember] = field(
        metadata=config(field_name="membership"), default=None
    )
    watchers: Optional[List[UserObject]] = field(
        metadata=config(field_name="watchers"), default=None
    )
