# THIS FILE IS GENERATED FROM github.com/GetStream/protocol/tree/main/openapi-gen/templates/python/type.tmpl
from dataclasses import dataclass, field
from dataclasses_json import config, dataclass_json

from typing import List, Optional


@dataclass_json
@dataclass
class UserRequest:
    id: str = field(metadata=config(field_name="id"))
    image: Optional[str] = field(metadata=config(field_name="image"), default=None)
    language: Optional[str] = field(
        metadata=config(field_name="language"), default=None
    )
    name: Optional[str] = field(metadata=config(field_name="name"), default=None)
    role: Optional[str] = field(metadata=config(field_name="role"), default=None)
    teams: Optional[List[str]] = field(
        metadata=config(field_name="teams"), default=None
    )
    custom: Optional[object] = field(metadata=config(field_name="custom"), default=None)
