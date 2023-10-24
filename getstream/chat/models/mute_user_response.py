# THIS FILE IS GENERATED FROM github.com/GetStream/protocol/tree/main/openapi-gen/templates/python/type.tmpl
from dataclasses import dataclass, field
from dataclasses_json import config, dataclass_json

from typing import List, Optional
from getstream.chat.models.user_mute import UserMute
from getstream.chat.models.own_user import OwnUser


@dataclass_json
@dataclass
class MuteUserResponse:
    duration: str = field(metadata=config(field_name="duration"))
    mute: Optional[UserMute] = field(metadata=config(field_name="mute"), default=None)
    mutes: Optional[List[UserMute]] = field(
        metadata=config(field_name="mutes"), default=None
    )
    own_user: Optional[OwnUser] = field(
        metadata=config(field_name="own_user"), default=None
    )
