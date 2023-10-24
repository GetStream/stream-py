# THIS FILE IS GENERATED FROM github.com/GetStream/protocol/tree/main/openapi-gen/templates/python/type.tmpl
from dataclasses import dataclass, field
from dataclasses_json import config, dataclass_json

from typing import Optional


@dataclass_json
@dataclass
class XiaomiConfigFields:
    enabled: bool = field(metadata=config(field_name="enabled"))
    package_name: Optional[str] = field(
        metadata=config(field_name="package_name"), default=None
    )
    secret: Optional[str] = field(metadata=config(field_name="secret"), default=None)
