# THIS FILE IS GENERATED FROM github.com/GetStream/protocol/tree/main/openapi-gen/templates/python/type.tmpl
from dataclasses import dataclass, field
from dataclasses_json import config, dataclass_json

from typing import Optional


@dataclass_json
@dataclass
class HuaweiConfigRequest:
    disabled: Optional[bool] = field(
        metadata=config(field_name="Disabled"), default=None
    )
    id: Optional[str] = field(metadata=config(field_name="id"), default=None)
    secret: Optional[str] = field(metadata=config(field_name="secret"), default=None)
