# THIS FILE IS GENERATED FROM github.com/GetStream/protocol/tree/main/openapi-gen/templates/python/type.tmpl
from dataclasses import dataclass, field
from dataclasses_json import config, dataclass_json

from typing import Optional


@dataclass_json
@dataclass
class ErrorResult:
    type: str = field(metadata=config(field_name="type"))
    description: object = field(metadata=config(field_name="description"))
    version: Optional[str] = field(metadata=config(field_name="version"), default=None)
    stacktrace: Optional[str] = field(
        metadata=config(field_name="stacktrace"), default=None
    )
