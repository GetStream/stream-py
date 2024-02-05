# THIS FILE IS GENERATED FROM github.com/GetStream/protocol/tree/main/openapi-gen/templates/python/type.tmpl
from dataclasses import dataclass, field
from dataclasses_json import config, dataclass_json


@dataclass_json
@dataclass
class UpdateExternalStorageResponse:
    type: str = field(metadata=config(field_name="type"))
    bucket: str = field(metadata=config(field_name="bucket"))
    duration: str = field(metadata=config(field_name="duration"))
    name: str = field(metadata=config(field_name="name"))
    path: str = field(metadata=config(field_name="path"))
