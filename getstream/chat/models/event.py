# THIS FILE IS GENERATED FROM github.com/GetStream/protocol/tree/main/openapi-gen/templates/python/type.tmpl
from dataclasses import dataclass, field
from dataclasses_json import config, dataclass_json

from typing import Optional
from datetime import datetime
from dateutil.parser import parse
from marshmallow import fields
from getstream.chat.models.reaction import Reaction
from getstream.chat.models.moderation_response import ModerationResponse
from getstream.chat.models.channel_response import ChannelResponse
from getstream.chat.models.user_object import UserObject
from getstream.chat.models.own_user import OwnUser
from getstream.chat.models.channel_member import ChannelMember
from getstream.chat.models.message import Message


@dataclass_json
@dataclass
class Event:
    created_at: datetime = field(
        metadata=config(
            field_name="created_at",
            encoder=lambda d: d.isoformat(),
            decoder=parse,
            mm_field=fields.DateTime(format="iso"),
        )
    )
    type: str = field(metadata=config(field_name="type"))
    automoderation_scores: Optional[ModerationResponse] = field(
        metadata=config(field_name="automoderation_scores"), default=None
    )
    channel_type: Optional[str] = field(
        metadata=config(field_name="channel_type"), default=None
    )
    team: Optional[str] = field(metadata=config(field_name="team"), default=None)
    watcher_count: Optional[int] = field(
        metadata=config(field_name="watcher_count"), default=None
    )
    channel: Optional[ChannelResponse] = field(
        metadata=config(field_name="channel"), default=None
    )
    channel_id: Optional[str] = field(
        metadata=config(field_name="channel_id"), default=None
    )
    created_by: Optional[UserObject] = field(
        metadata=config(field_name="created_by"), default=None
    )
    me: Optional[OwnUser] = field(metadata=config(field_name="me"), default=None)
    parent_id: Optional[str] = field(
        metadata=config(field_name="parent_id"), default=None
    )
    user: Optional[UserObject] = field(metadata=config(field_name="user"), default=None)
    user_id: Optional[str] = field(metadata=config(field_name="user_id"), default=None)
    cid: Optional[str] = field(metadata=config(field_name="cid"), default=None)
    member: Optional[ChannelMember] = field(
        metadata=config(field_name="member"), default=None
    )
    message: Optional[Message] = field(
        metadata=config(field_name="message"), default=None
    )
    reason: Optional[str] = field(metadata=config(field_name="reason"), default=None)
    automoderation: Optional[bool] = field(
        metadata=config(field_name="automoderation"), default=None
    )
    connection_id: Optional[str] = field(
        metadata=config(field_name="connection_id"), default=None
    )
    reaction: Optional[Reaction] = field(
        metadata=config(field_name="reaction"), default=None
    )
