# THIS FILE IS GENERATED FROM github.com/GetStream/protocol/tree/main/openapi-gen/templates/python/type.tmpl
from dataclasses import dataclass, field
from dataclasses_json import config, dataclass_json

from typing import Optional


@dataclass_json
@dataclass
class ConnectUserDetailsRequest:
    id: str = field(metadata=config(field_name="id"))
    language: Optional[str] = field(
        metadata=config(field_name="language"), default=None
    )
    name: Optional[str] = field(metadata=config(field_name="name"), default=None)
    custom: Optional[object] = field(metadata=config(field_name="custom"), default=None)
    image: Optional[str] = field(metadata=config(field_name="image"), default=None)
