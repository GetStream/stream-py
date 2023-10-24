# THIS FILE IS GENERATED FROM github.com/GetStream/protocol/tree/main/openapi-gen/templates/python/type.tmpl
from dataclasses import dataclass, field
from dataclasses_json import config, dataclass_json

from typing import List, Optional
from getstream.chat.models.channel_member_request import ChannelMemberRequest
from getstream.chat.models.channel_request import ChannelRequest
from getstream.chat.models.user_object_request import UserObjectRequest
from getstream.chat.models.message_request import MessageRequest


@dataclass_json
@dataclass
class UpdateChannelRequest:
    add_moderators: List[str] = field(metadata=config(field_name="add_moderators"))
    demote_moderators: List[str] = field(
        metadata=config(field_name="demote_moderators")
    )
    remove_members: List[str] = field(metadata=config(field_name="remove_members"))
    assign_roles: Optional[List[ChannelMemberRequest]] = field(
        metadata=config(field_name="assign_roles"), default=None
    )
    invites: Optional[List[ChannelMemberRequest]] = field(
        metadata=config(field_name="invites"), default=None
    )
    reject_invite: Optional[bool] = field(
        metadata=config(field_name="reject_invite"), default=None
    )
    skip_push: Optional[bool] = field(
        metadata=config(field_name="skip_push"), default=None
    )
    user_id: Optional[str] = field(metadata=config(field_name="user_id"), default=None)
    accept_invite: Optional[bool] = field(
        metadata=config(field_name="accept_invite"), default=None
    )
    cooldown: Optional[int] = field(
        metadata=config(field_name="cooldown"), default=None
    )
    message: Optional[MessageRequest] = field(
        metadata=config(field_name="message"), default=None
    )
    user: Optional[UserObjectRequest] = field(
        metadata=config(field_name="user"), default=None
    )
    add_members: Optional[List[ChannelMemberRequest]] = field(
        metadata=config(field_name="add_members"), default=None
    )
    data: Optional[ChannelRequest] = field(
        metadata=config(field_name="data"), default=None
    )
    hide_history: Optional[bool] = field(
        metadata=config(field_name="hide_history"), default=None
    )
