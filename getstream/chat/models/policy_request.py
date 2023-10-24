# THIS FILE IS GENERATED FROM github.com/GetStream/protocol/tree/main/openapi-gen/templates/python/type.tmpl
from dataclasses import dataclass, field
from dataclasses_json import config, dataclass_json

from typing import List, Optional


@dataclass_json
@dataclass
class PolicyRequest:
    name: str = field(metadata=config(field_name="name"))
    priority: int = field(metadata=config(field_name="priority"))
    action: Optional[str] = field(metadata=config(field_name="action"), default=None)
    owner: Optional[bool] = field(metadata=config(field_name="owner"), default=None)
    resources: Optional[List[str]] = field(
        metadata=config(field_name="resources"), default=None
    )
    roles: Optional[List[str]] = field(
        metadata=config(field_name="roles"), default=None
    )
