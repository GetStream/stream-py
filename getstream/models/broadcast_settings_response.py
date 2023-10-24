# THIS FILE IS GENERATED FROM github.com/GetStream/protocol/tree/main/openapi-gen/templates/python/type.tmpl
from dataclasses import dataclass, field
from dataclasses_json import config, dataclass_json

from getstream.models.hls_settings_response import HlssettingsResponse


@dataclass_json
@dataclass
class BroadcastSettingsResponse:
    enabled: bool = field(metadata=config(field_name="enabled"))
    hls: HlssettingsResponse = field(metadata=config(field_name="hls"))
