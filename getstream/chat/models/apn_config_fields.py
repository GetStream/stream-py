# THIS FILE IS GENERATED FROM github.com/GetStream/protocol/tree/main/openapi-gen/templates/python/type.tmpl
from dataclasses import dataclass, field
from dataclasses_json import config, dataclass_json

from typing import Optional


@dataclass_json
@dataclass
class ApnconfigFields:
    development: bool = field(metadata=config(field_name="development"))
    notification_template: str = field(
        metadata=config(field_name="notification_template")
    )
    enabled: bool = field(metadata=config(field_name="enabled"))
    auth_key: Optional[str] = field(
        metadata=config(field_name="auth_key"), default=None
    )
    auth_type: Optional[str] = field(
        metadata=config(field_name="auth_type"), default=None
    )
    host: Optional[str] = field(metadata=config(field_name="host"), default=None)
    key_id: Optional[str] = field(metadata=config(field_name="key_id"), default=None)
    p_12_cert: Optional[str] = field(
        metadata=config(field_name="p12_cert"), default=None
    )
    bundle_id: Optional[str] = field(
        metadata=config(field_name="bundle_id"), default=None
    )
    team_id: Optional[str] = field(metadata=config(field_name="team_id"), default=None)
