# THIS FILE IS GENERATED FROM github.com/GetStream/protocol/tree/main/openapi-gen/templates/python/type.tmpl
from dataclasses import dataclass, field
from dataclasses_json import config, dataclass_json

from typing import Optional


@dataclass_json
@dataclass
class FieldRequest:
    value: Optional[str] = field(metadata=config(field_name="value"), default=None)
    short: Optional[bool] = field(metadata=config(field_name="short"), default=None)
    title: Optional[str] = field(metadata=config(field_name="title"), default=None)
