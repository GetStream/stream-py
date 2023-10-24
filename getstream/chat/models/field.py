# THIS FILE IS GENERATED FROM github.com/GetStream/protocol/tree/main/openapi-gen/templates/python/type.tmpl
from dataclasses import dataclass, field
from dataclasses_json import config, dataclass_json


@dataclass_json
@dataclass
class Field:
    short: bool = field(metadata=config(field_name="short"))
    title: str = field(metadata=config(field_name="title"))
    value: str = field(metadata=config(field_name="value"))
