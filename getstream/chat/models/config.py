# THIS FILE IS GENERATED FROM github.com/GetStream/protocol/tree/main/openapi-gen/templates/python/type.tmpl
from dataclasses import dataclass, field
from dataclasses_json import config, dataclass_json

from typing import Dict, Optional


@dataclass_json
@dataclass
class Config:
    app_certificate: str = field(metadata=config(field_name="app_certificate"))
    app_id: str = field(metadata=config(field_name="app_id"))
    default_role: Optional[str] = field(
        metadata=config(field_name="default_role"), default=None
    )
    role_map: Optional[Dict[str, str]] = field(
        metadata=config(field_name="role_map"), default=None
    )
