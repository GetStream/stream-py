# THIS FILE IS GENERATED FROM github.com/GetStream/protocol/tree/main/openapi-gen/templates/python/type.tmpl
from dataclasses import dataclass, field
from dataclasses_json import config, dataclass_json

from typing import List, Dict, Optional


@dataclass_json
@dataclass
class Permission:
    custom: bool = field(metadata=config(field_name="custom"))
    description: str = field(metadata=config(field_name="description"))
    name: str = field(metadata=config(field_name="name"))
    same_team: bool = field(metadata=config(field_name="same_team"))
    tags: List[str] = field(metadata=config(field_name="tags"))
    action: str = field(metadata=config(field_name="action"))
    owner: bool = field(metadata=config(field_name="owner"))
    id: str = field(metadata=config(field_name="id"))
    level: str = field(metadata=config(field_name="level"))
    condition: Optional[Dict[str, object]] = field(
        metadata=config(field_name="condition"), default=None
    )
