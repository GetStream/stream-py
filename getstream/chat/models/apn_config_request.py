# THIS FILE IS GENERATED FROM github.com/GetStream/protocol/tree/main/openapi-gen/templates/python/type.tmpl
from dataclasses import dataclass, field
from dataclasses_json import config, dataclass_json

from typing import Optional


@dataclass_json
@dataclass
class ApnconfigRequest:
    development: Optional[bool] = field(
        metadata=config(field_name="development"), default=None
    )
    host: Optional[str] = field(metadata=config(field_name="host"), default=None)
    key_id: Optional[str] = field(metadata=config(field_name="key_id"), default=None)
    notification_template: Optional[str] = field(
        metadata=config(field_name="notification_template"), default=None
    )
    disabled: Optional[bool] = field(
        metadata=config(field_name="Disabled"), default=None
    )
    auth_key: Optional[str] = field(
        metadata=config(field_name="auth_key"), default=None
    )
    auth_type: Optional[str] = field(
        metadata=config(field_name="auth_type"), default=None
    )
    bundle_id: Optional[str] = field(
        metadata=config(field_name="bundle_id"), default=None
    )
    p_12_cert: Optional[str] = field(
        metadata=config(field_name="p12_cert"), default=None
    )
    team_id: Optional[str] = field(metadata=config(field_name="team_id"), default=None)
