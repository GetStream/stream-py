# THIS FILE IS GENERATED FROM github.com/GetStream/protocol/tree/main/openapi-gen/templates/python/type.tmpl
from dataclasses import dataclass, field
from dataclasses_json import config, dataclass_json

from typing import Optional
from datetime import datetime
from dateutil.parser import parse
from marshmallow import fields
from getstream.chat.models.channel_member import ChannelMember
from getstream.chat.models.user_object import UserObject


@dataclass_json
@dataclass
class MemberAddedEvent:
    channel_id: str = field(metadata=config(field_name="channel_id"))
    channel_type: str = field(metadata=config(field_name="channel_type"))
    cid: str = field(metadata=config(field_name="cid"))
    created_at: datetime = field(
        metadata=config(
            field_name="created_at",
            encoder=lambda d: d.isoformat(),
            decoder=parse,
            mm_field=fields.DateTime(format="iso"),
        )
    )
    type: str = field(metadata=config(field_name="type"))
    user: Optional[UserObject] = field(metadata=config(field_name="user"), default=None)
    member: Optional[ChannelMember] = field(
        metadata=config(field_name="member"), default=None
    )
    team: Optional[str] = field(metadata=config(field_name="team"), default=None)
