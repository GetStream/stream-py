# THIS FILE IS GENERATED FROM github.com/GetStream/protocol/tree/main/openapi-gen/templates/python/type.tmpl
from dataclasses import dataclass, field
from dataclasses_json import config, dataclass_json

from typing import List, Optional
from datetime import datetime
from dateutil.parser import parse
from marshmallow import fields
from getstream.chat.models.channel_config import ChannelConfig
from getstream.chat.models.user_object import UserObject
from getstream.chat.models.channel_member import ChannelMember


@dataclass_json
@dataclass
class Channel:
    disabled: bool = field(metadata=config(field_name="disabled"))
    type: str = field(metadata=config(field_name="type"))
    updated_at: datetime = field(
        metadata=config(
            field_name="updated_at",
            encoder=lambda d: d.isoformat(),
            decoder=parse,
            mm_field=fields.DateTime(format="iso"),
        )
    )
    auto_translation_language: str = field(
        metadata=config(field_name="auto_translation_language")
    )
    frozen: bool = field(metadata=config(field_name="frozen"))
    created_at: datetime = field(
        metadata=config(
            field_name="created_at",
            encoder=lambda d: d.isoformat(),
            decoder=parse,
            mm_field=fields.DateTime(format="iso"),
        )
    )
    cid: str = field(metadata=config(field_name="cid"))
    id: str = field(metadata=config(field_name="id"))
    cooldown: Optional[int] = field(
        metadata=config(field_name="cooldown"), default=None
    )
    team: Optional[str] = field(metadata=config(field_name="team"), default=None)
    auto_translation_enabled: Optional[bool] = field(
        metadata=config(field_name="auto_translation_enabled"), default=None
    )
    config_overrides: Optional[ChannelConfig] = field(
        metadata=config(field_name="config_overrides"), default=None
    )
    invites: Optional[List[ChannelMember]] = field(
        metadata=config(field_name="invites"), default=None
    )
    truncated_by: Optional[UserObject] = field(
        metadata=config(field_name="truncated_by"), default=None
    )
    created_by: Optional[UserObject] = field(
        metadata=config(field_name="created_by"), default=None
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
    last_message_at: Optional[datetime] = field(
        metadata=config(
            field_name="last_message_at",
            encoder=lambda d: d.isoformat() if d is not None else None,
            decoder=parse,
            mm_field=fields.DateTime(format="iso"),
        ),
        default=None,
    )
    members: Optional[List[ChannelMember]] = field(
        metadata=config(field_name="members"), default=None
    )
    config: Optional[ChannelConfig] = field(
        metadata=config(field_name="config"), default=None
    )
    member_count: Optional[int] = field(
        metadata=config(field_name="member_count"), default=None
    )
