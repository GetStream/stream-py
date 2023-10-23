# THIS FILE IS GENERATED FROM github.com/GetStream/protocol/tree/main/openapi-gen/templates/python/type.tmpl
from dataclasses import dataclass, field
from dataclasses_json import config, dataclass_json

from typing import Optional
from getstream.chat.models.agora_call import AgoraCall
from getstream.chat.models.hms_call import Hmscall


@dataclass_json
@dataclass
class Call:
    id: str = field(metadata=config(field_name="id"))
    provider: str = field(metadata=config(field_name="provider"))
    type: str = field(metadata=config(field_name="type"))
    agora: Optional[AgoraCall] = field(
        metadata=config(field_name="agora"), default=None
    )
    hms: Optional[Hmscall] = field(metadata=config(field_name="hms"), default=None)
