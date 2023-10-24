# THIS FILE IS GENERATED FROM github.com/GetStream/protocol/tree/main/openapi-gen/templates/python/type.tmpl
from dataclasses import dataclass, field
from dataclasses_json import config, dataclass_json

from typing import Optional
from getstream.models.layout_settings_request import LayoutSettingsRequest


@dataclass_json
@dataclass
class RecordSettingsRequest:
    mode: str = field(metadata=config(field_name="mode"))
    audio_only: Optional[bool] = field(
        metadata=config(field_name="audio_only"), default=None
    )
    layout: Optional[LayoutSettingsRequest] = field(
        metadata=config(field_name="layout"), default=None
    )
    quality: Optional[str] = field(metadata=config(field_name="quality"), default=None)
