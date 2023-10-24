# THIS FILE IS GENERATED FROM github.com/GetStream/protocol/tree/main/openapi-gen/templates/python/type.tmpl
from dataclasses import dataclass, field
from dataclasses_json import config, dataclass_json

from typing import Optional


@dataclass_json
@dataclass
class DeviceFields:
    id: str = field(metadata=config(field_name="id"))
    push_provider: str = field(metadata=config(field_name="push_provider"))
    push_provider_name: Optional[str] = field(
        metadata=config(field_name="push_provider_name"), default=None
    )
    voip: Optional[bool] = field(metadata=config(field_name="voip"), default=None)
