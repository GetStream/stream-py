# THIS FILE IS GENERATED FROM github.com/GetStream/protocol/tree/main/openapi-gen/templates/python/type.tmpl
from dataclasses import dataclass, field
from dataclasses_json import config, dataclass_json

from typing import Optional


@dataclass_json
@dataclass
class LabelThresholds:
    block: Optional[float] = field(metadata=config(field_name="block"), default=None)
    flag: Optional[float] = field(metadata=config(field_name="flag"), default=None)
