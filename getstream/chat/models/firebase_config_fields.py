# THIS FILE IS GENERATED FROM github.com/GetStream/protocol/tree/main/openapi-gen/templates/python/type.tmpl
from dataclasses import dataclass, field
from dataclasses_json import config, dataclass_json

from typing import Optional


@dataclass_json
@dataclass
class FirebaseConfigFields:
    data_template: str = field(metadata=config(field_name="data_template"))
    enabled: bool = field(metadata=config(field_name="enabled"))
    notification_template: str = field(
        metadata=config(field_name="notification_template")
    )
    apn_template: str = field(metadata=config(field_name="apn_template"))
    credentials_json: Optional[str] = field(
        metadata=config(field_name="credentials_json"), default=None
    )
    server_key: Optional[str] = field(
        metadata=config(field_name="server_key"), default=None
    )
