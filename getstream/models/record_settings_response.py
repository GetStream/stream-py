# THIS FILE IS GENERATED FROM github.com/GetStream/protocol/tree/main/openapi-gen/templates/python/type.tmpl
from dataclasses import dataclass, field
from dataclasses_json import config, dataclass_json

from getstream.models.layout_settings import LayoutSettings


@dataclass_json
@dataclass
class RecordSettingsResponse:
    layout: LayoutSettings = field(metadata=config(field_name="layout"))
    mode: str = field(metadata=config(field_name="mode"))
    quality: str = field(metadata=config(field_name="quality"))
    audio_only: bool = field(metadata=config(field_name="audio_only"))
