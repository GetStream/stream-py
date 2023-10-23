# THIS FILE IS GENERATED FROM github.com/GetStream/protocol/tree/main/openapi-gen/templates/python/type.tmpl
from dataclasses import dataclass, field
from dataclasses_json import config, dataclass_json

from typing import Optional


@dataclass_json
@dataclass
class ActionRequest:
    value: Optional[str] = field(metadata=config(field_name="value"), default=None)
    name: Optional[str] = field(metadata=config(field_name="name"), default=None)
    style: Optional[str] = field(metadata=config(field_name="style"), default=None)
    text: Optional[str] = field(metadata=config(field_name="text"), default=None)
    type: Optional[str] = field(metadata=config(field_name="type"), default=None)
