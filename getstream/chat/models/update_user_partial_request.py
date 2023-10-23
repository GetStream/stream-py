# THIS FILE IS GENERATED FROM github.com/GetStream/protocol/tree/main/openapi-gen/templates/python/type.tmpl
from dataclasses import dataclass, field
from dataclasses_json import config, dataclass_json

from typing import Dict, List


@dataclass_json
@dataclass
class UpdateUserPartialRequest:
    unset: List[str] = field(metadata=config(field_name="unset"))
    id: str = field(metadata=config(field_name="id"))
    set: Dict[str, object] = field(metadata=config(field_name="set"))
