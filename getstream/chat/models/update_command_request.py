# THIS FILE IS GENERATED FROM github.com/GetStream/protocol/tree/main/openapi-gen/templates/python/type.tmpl
from dataclasses import dataclass, field
from dataclasses_json import config, dataclass_json

from typing import Optional


@dataclass_json
@dataclass
class UpdateCommandRequest:
    description: str = field(metadata=config(field_name="description"))
    name: Optional[str] = field(metadata=config(field_name="Name"), default=None)
    args: Optional[str] = field(metadata=config(field_name="args"), default=None)
    set: Optional[str] = field(metadata=config(field_name="set"), default=None)
