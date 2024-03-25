# THIS FILE IS GENERATED FROM github.com/GetStream/protocol/tree/main/openapi-gen/templates/python/type.tmpl
from dataclasses import dataclass, field
from dataclasses_json import config, dataclass_json

from typing import List
from getstream.models.layout_settings import LayoutSettings


@dataclass_json
@dataclass
class HlssettingsResponse:
    auto_on: bool = field(metadata=config(field_name="auto_on"))
    enabled: bool = field(metadata=config(field_name="enabled"))
    layout: LayoutSettings = field(metadata=config(field_name="layout"))
    quality_tracks: List[str] = field(metadata=config(field_name="quality_tracks"))
