# THIS FILE IS GENERATED FROM github.com/GetStream/protocol/tree/main/openapi-gen/templates/python/type.tmpl
from dataclasses import dataclass, field
from dataclasses_json import config, dataclass_json

from typing import Optional


@dataclass_json
@dataclass
class SortParamRequest:
    direction: Optional[int] = field(
        metadata=config(field_name="direction"), default=None
    )
    field: Optional[str] = field(metadata=config(field_name="field"), default=None)
