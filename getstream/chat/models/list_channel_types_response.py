# THIS FILE IS GENERATED FROM github.com/GetStream/protocol/tree/main/openapi-gen/templates/python/type.tmpl
from dataclasses import dataclass, field
from dataclasses_json import config, dataclass_json

from typing import Dict
from getstream.chat.models.channel_type_config import ChannelTypeConfig


@dataclass_json
@dataclass
class ListChannelTypesResponse:
    channel_types: Dict[str, ChannelTypeConfig] = field(
        metadata=config(field_name="channel_types")
    )
    duration: str = field(metadata=config(field_name="duration"))
