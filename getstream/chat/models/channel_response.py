# THIS FILE IS GENERATED FROM github.com/GetStream/protocol/tree/main/openapi-gen/templates/python/type.tmpl
from dataclasses import dataclass, field
from dataclasses_json import config, dataclass_json

from typing import List, Optional
from datetime import datetime
from dateutil.parser import parse
from marshmallow import fields
from getstream.chat.models.user_object import UserObject
from getstream.chat.models.channel_member import ChannelMember
from getstream.chat.models.channel_config_with_info import ChannelConfigWithInfo


@dataclass_json
@dataclass
class ChannelResponse:
    disabled: bool = field(metadata=config(field_name="disabled"))
    frozen: bool = field(metadata=config(field_name="frozen"))
    cid: str = field(metadata=config(field_name="cid"))
    id: str = field(metadata=config(field_name="id"))
    type: str = field(metadata=config(field_name="type"))
    auto_translation_language: Optional[str] = field(
        metadata=config(field_name="auto_translation_language"), default=None
    )
    hide_messages_before: Optional[datetime] = field(
        metadata=config(
            field_name="hide_messages_before",
            encoder=lambda d: d.isoformat() if d is not None else None,
            decoder=parse,
            mm_field=fields.DateTime(format="iso"),
        ),
        default=None,
    )
    mute_expires_at: Optional[datetime] = field(
        metadata=config(
            field_name="mute_expires_at",
            encoder=lambda d: d.isoformat() if d is not None else None,
            decoder=parse,
            mm_field=fields.DateTime(format="iso"),
        ),
        default=None,
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
    updated_at: Optional[datetime] = field(
        metadata=config(
            field_name="updated_at",
            encoder=lambda d: d.isoformat() if d is not None else None,
            decoder=parse,
            mm_field=fields.DateTime(format="iso"),
        ),
        default=None,
    )
    cooldown: Optional[int] = field(
        metadata=config(field_name="cooldown"), default=None
    )
    created_by: Optional[UserObject] = field(
        metadata=config(field_name="created_by"), default=None
    )
    last_message_at: Optional[datetime] = field(
        metadata=config(
            field_name="last_message_at",
            encoder=lambda d: d.isoformat() if d is not None else None,
            decoder=parse,
            mm_field=fields.DateTime(format="iso"),
        ),
        default=None,
    )
    own_capabilities: Optional[List[str]] = field(
        metadata=config(field_name="own_capabilities"), default=None
    )
    truncated_by: Optional[UserObject] = field(
        metadata=config(field_name="truncated_by"), default=None
    )
    team: Optional[str] = field(metadata=config(field_name="team"), default=None)
    auto_translation_enabled: Optional[bool] = field(
        metadata=config(field_name="auto_translation_enabled"), default=None
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
    member_count: Optional[int] = field(
        metadata=config(field_name="member_count"), default=None
    )
    members: Optional[List[ChannelMember]] = field(
        metadata=config(field_name="members"), default=None
    )
    muted: Optional[bool] = field(metadata=config(field_name="muted"), default=None)
    config_: Optional[ChannelConfigWithInfo] = field(
        metadata=config(field_name="config"), default=None
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
    hidden: Optional[bool] = field(metadata=config(field_name="hidden"), default=None)
