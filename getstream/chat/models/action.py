# THIS FILE IS GENERATED FROM github.com/GetStream/protocol/tree/main/openapi-gen/templates/python/type.tmpl
from dataclasses import dataclass, field
from dataclasses_json import config, dataclass_json

from typing import Optional


@dataclass_json
@dataclass
class Action:
    name: str = field(metadata=config(field_name="name"))
    text: str = field(metadata=config(field_name="text"))
    type: str = field(metadata=config(field_name="type"))
    style: Optional[str] = field(metadata=config(field_name="style"), default=None)
    value: Optional[str] = field(metadata=config(field_name="value"), default=None)
