# THIS FILE IS GENERATED FROM github.com/GetStream/protocol/tree/main/openapi-gen/templates/python/type.tmpl
from dataclasses import dataclass, field
from dataclasses_json import config, dataclass_json

from getstream.chat.models.hls_settings import Hlssettings


@dataclass_json
@dataclass
class BroadcastSettings:
    hls: Hlssettings = field(metadata=config(field_name="hls"))
    enabled: bool = field(metadata=config(field_name="enabled"))
