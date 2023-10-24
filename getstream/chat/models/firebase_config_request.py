# THIS FILE IS GENERATED FROM github.com/GetStream/protocol/tree/main/openapi-gen/templates/python/type.tmpl
from dataclasses import dataclass, field
from dataclasses_json import config, dataclass_json

from typing import Optional


@dataclass_json
@dataclass
class FirebaseConfigRequest:
    disabled: Optional[bool] = field(
        metadata=config(field_name="Disabled"), default=None
    )
    apn_template: Optional[str] = field(
        metadata=config(field_name="apn_template"), default=None
    )
    credentials_json: Optional[str] = field(
        metadata=config(field_name="credentials_json"), default=None
    )
    data_template: Optional[str] = field(
        metadata=config(field_name="data_template"), default=None
    )
    notification_template: Optional[str] = field(
        metadata=config(field_name="notification_template"), default=None
    )
    server_key: Optional[str] = field(
        metadata=config(field_name="server_key"), default=None
    )
