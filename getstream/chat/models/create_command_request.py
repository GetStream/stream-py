# THIS FILE IS GENERATED FROM github.com/GetStream/protocol/tree/main/openapi-gen/templates/python/type.tmpl
from dataclasses import dataclass, field
from dataclasses_json import config, dataclass_json

from typing import Optional


@dataclass_json
@dataclass
class CreateCommandRequest:
    name: str = field(metadata=config(field_name="name"))
    description: str = field(metadata=config(field_name="description"))
    set: Optional[str] = field(metadata=config(field_name="set"), default=None)
    args: Optional[str] = field(metadata=config(field_name="args"), default=None)
