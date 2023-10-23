# THIS FILE IS GENERATED FROM github.com/GetStream/protocol/tree/main/openapi-gen/templates/python/type.tmpl
from dataclasses import dataclass, field
from dataclasses_json import config, dataclass_json

from typing import List, Optional
from getstream.chat.models.own_user import OwnUser
from getstream.chat.models.channel_mute import ChannelMute


@dataclass_json
@dataclass
class MuteChannelResponse:
    duration: str = field(metadata=config(field_name="duration"))
    channel_mute: Optional[ChannelMute] = field(
        metadata=config(field_name="channel_mute"), default=None
    )
    channel_mutes: Optional[List[ChannelMute]] = field(
        metadata=config(field_name="channel_mutes"), default=None
    )
    own_user: Optional[OwnUser] = field(
        metadata=config(field_name="own_user"), default=None
    )
