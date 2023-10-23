# THIS FILE IS GENERATED FROM github.com/GetStream/protocol/tree/main/openapi-gen/templates/python/type.tmpl
from dataclasses import dataclass, field
from dataclasses_json import config, dataclass_json

from typing import Optional
from datetime import datetime
from dateutil.parser import parse
from marshmallow import fields
from getstream.chat.models.channel_response_request import ChannelResponseRequest
from getstream.chat.models.own_user_request import OwnUserRequest
from getstream.chat.models.channel_member_request import ChannelMemberRequest
from getstream.chat.models.user_object_request import UserObjectRequest
from getstream.chat.models.message_request_1 import MessageRequest1
from getstream.chat.models.moderation_response_request import ModerationResponseRequest
from getstream.chat.models.reaction_request import ReactionRequest


@dataclass_json
@dataclass
class EventRequest:
    type: str = field(metadata=config(field_name="type"))
    channel_id: Optional[str] = field(
        metadata=config(field_name="channel_id"), default=None
    )
    cid: Optional[str] = field(metadata=config(field_name="cid"), default=None)
    created_by: Optional[UserObjectRequest] = field(
        metadata=config(field_name="created_by"), default=None
    )
    message: Optional[MessageRequest1] = field(
        metadata=config(field_name="message"), default=None
    )
    user_id: Optional[str] = field(metadata=config(field_name="user_id"), default=None)
    automoderation: Optional[bool] = field(
        metadata=config(field_name="automoderation"), default=None
    )
    channel_type: Optional[str] = field(
        metadata=config(field_name="channel_type"), default=None
    )
    automoderation_scores: Optional[ModerationResponseRequest] = field(
        metadata=config(field_name="automoderation_scores"), default=None
    )
    parent_id: Optional[str] = field(
        metadata=config(field_name="parent_id"), default=None
    )
    reaction: Optional[ReactionRequest] = field(
        metadata=config(field_name="reaction"), default=None
    )
    reason: Optional[str] = field(metadata=config(field_name="reason"), default=None)
    user: Optional[UserObjectRequest] = field(
        metadata=config(field_name="user"), default=None
    )
    watcher_count: Optional[int] = field(
        metadata=config(field_name="watcher_count"), default=None
    )
    connection_id: Optional[str] = field(
        metadata=config(field_name="connection_id"), default=None
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
    me: Optional[OwnUserRequest] = field(metadata=config(field_name="me"), default=None)
    member: Optional[ChannelMemberRequest] = field(
        metadata=config(field_name="member"), default=None
    )
    team: Optional[str] = field(metadata=config(field_name="team"), default=None)
    channel: Optional[ChannelResponseRequest] = field(
        metadata=config(field_name="channel"), default=None
    )
