# THIS FILE IS GENERATED FROM github.com/GetStream/protocol/tree/main/openapi-gen/templates/python/type.tmpl
from dataclasses import dataclass, field
from dataclasses_json import config, dataclass_json

from typing import List, Optional
from getstream.models.layout_settings_request import LayoutSettingsRequest


@dataclass_json
@dataclass
class HlssettingsRequest:
    layout: Optional[LayoutSettingsRequest] = field(
        metadata=config(field_name="layout"), default=None
    )
    quality_tracks: Optional[List[str]] = field(
        metadata=config(field_name="quality_tracks"), default=None
    )
    auto_on: Optional[bool] = field(metadata=config(field_name="auto_on"), default=None)
    enabled: Optional[bool] = field(metadata=config(field_name="enabled"), default=None)
