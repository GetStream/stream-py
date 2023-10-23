# THIS FILE IS GENERATED FROM github.com/GetStream/protocol/tree/main/openapi-gen/templates/python/type.tmpl
from dataclasses import dataclass, field
from dataclasses_json import config, dataclass_json

from typing import Optional


@dataclass_json
@dataclass
class CreateImportRequest:
    path: str = field(metadata=config(field_name="path"))
    mode: Optional[str] = field(metadata=config(field_name="mode"), default=None)
