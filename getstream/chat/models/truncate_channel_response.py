# THIS FILE IS GENERATED FROM github.com/GetStream/protocol/tree/main/openapi-gen/templates/python/type.tmpl
from dataclasses import dataclass, field
from dataclasses_json import config, dataclass_json

from typing import Optional
from getstream.chat.models.channel_response import ChannelResponse
from getstream.chat.models.message import Message


@dataclass_json
@dataclass
class TruncateChannelResponse:
    duration: str = field(metadata=config(field_name="duration"))
    channel: Optional[ChannelResponse] = field(
        metadata=config(field_name="channel"), default=None
    )
    message: Optional[Message] = field(
        metadata=config(field_name="message"), default=None
    )
