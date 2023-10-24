# THIS FILE IS GENERATED FROM github.com/GetStream/protocol/tree/main/openapi-gen/templates/python/type.tmpl
from dataclasses import dataclass, field
from dataclasses_json import config, dataclass_json

from typing import List


@dataclass_json
@dataclass
class PolicyRequest1:
    name: str = field(metadata=config(field_name="name"))
    owner: bool = field(metadata=config(field_name="owner"))
    priority: int = field(metadata=config(field_name="priority"))
    resources: List[str] = field(metadata=config(field_name="resources"))
    roles: List[str] = field(metadata=config(field_name="roles"))
    action: str = field(metadata=config(field_name="action"))
