# THIS FILE IS GENERATED FROM github.com/GetStream/protocol/tree/main/openapi-gen/templates/python/type.tmpl
from dataclasses import dataclass, field
from dataclasses_json import config, dataclass_json

from typing import List
from getstream.chat.models.channel_state_response_fields import (
    ChannelStateResponseFields,
)


@dataclass_json
@dataclass
class ChannelsResponse:
    channels: List[ChannelStateResponseFields] = field(
        metadata=config(field_name="channels")
    )
    duration: str = field(metadata=config(field_name="duration"))
