# THIS FILE IS GENERATED FROM github.com/GetStream/protocol/tree/main/openapi-gen/templates/python/type.tmpl
from dataclasses import dataclass, field
from dataclasses_json import config, dataclass_json


@dataclass_json
@dataclass
class ExternalStorageResponse:
    type: str = field(metadata=config(field_name="type"))
    bucket: str = field(metadata=config(field_name="bucket"))
    name: str = field(metadata=config(field_name="name"))
    path: str = field(metadata=config(field_name="path"))
