# THIS FILE IS GENERATED FROM github.com/GetStream/protocol/tree/main/openapi-gen/templates/python/type.tmpl
from dataclasses import dataclass, field
from dataclasses_json import config, dataclass_json


@dataclass_json
@dataclass
class RecordSettings:
    audio_only: bool = field(metadata=config(field_name="audio_only"))
    mode: str = field(metadata=config(field_name="mode"))
    quality: str = field(metadata=config(field_name="quality"))
