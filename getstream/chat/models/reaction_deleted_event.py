# THIS FILE IS GENERATED FROM github.com/GetStream/protocol/tree/main/openapi-gen/templates/python/type.tmpl
from dataclasses import dataclass, field
from dataclasses_json import config, dataclass_json

from typing import List, Optional
from datetime import datetime
from dateutil.parser import parse
from marshmallow import fields
from getstream.chat.models.message import Message
from getstream.chat.models.user_object import UserObject
from getstream.chat.models.reaction import Reaction


@dataclass_json
@dataclass
class ReactionDeletedEvent:
    created_at: datetime = field(
        metadata=config(
            field_name="created_at",
            encoder=lambda d: d.isoformat(),
            decoder=parse,
            mm_field=fields.DateTime(format="iso"),
        )
    )
    type: str = field(metadata=config(field_name="type"))
    channel_id: str = field(metadata=config(field_name="channel_id"))
    channel_type: str = field(metadata=config(field_name="channel_type"))
    cid: str = field(metadata=config(field_name="cid"))
    message: Optional[Message] = field(
        metadata=config(field_name="message"), default=None
    )
    thread_participants: Optional[List[UserObject]] = field(
        metadata=config(field_name="thread_participants"), default=None
    )
    user: Optional[UserObject] = field(metadata=config(field_name="user"), default=None)
    reaction: Optional[Reaction] = field(
        metadata=config(field_name="reaction"), default=None
    )
    team: Optional[str] = field(metadata=config(field_name="team"), default=None)
