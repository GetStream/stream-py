# THIS FILE IS GENERATED FROM github.com/GetStream/protocol/tree/main/openapi-gen/templates/python/type.tmpl
from dataclasses import dataclass, field
from dataclasses_json import config, dataclass_json

from typing import List, Optional
from getstream.chat.models.channel_response import ChannelResponse
from getstream.chat.models.message import Message


@dataclass_json
@dataclass
class ChannelMessages:
    messages: List[Message] = field(metadata=config(field_name="messages"))
    channel: Optional[ChannelResponse] = field(
        metadata=config(field_name="channel"), default=None
    )
