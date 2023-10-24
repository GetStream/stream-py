# THIS FILE IS GENERATED FROM github.com/GetStream/protocol/tree/main/openapi-gen/templates/python/type.tmpl
from dataclasses import dataclass, field
from dataclasses_json import config, dataclass_json

from typing import Dict, Optional
from getstream.chat.models.channel import Channel
from getstream.chat.models.message import Message
from getstream.chat.models.user_object import UserObject


@dataclass_json
@dataclass
class PendingMessage:
    user: Optional[UserObject] = field(metadata=config(field_name="user"), default=None)
    channel: Optional[Channel] = field(
        metadata=config(field_name="channel"), default=None
    )
    message: Optional[Message] = field(
        metadata=config(field_name="message"), default=None
    )
    metadata: Optional[Dict[str, str]] = field(
        metadata=config(field_name="metadata"), default=None
    )
