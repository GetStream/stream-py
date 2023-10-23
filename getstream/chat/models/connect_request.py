# THIS FILE IS GENERATED FROM github.com/GetStream/protocol/tree/main/openapi-gen/templates/python/type.tmpl
from dataclasses import dataclass, field
from dataclasses_json import config, dataclass_json

from typing import Optional
from getstream.chat.models.device_fields import DeviceFields
from getstream.chat.models.user_object import UserObject


@dataclass_json
@dataclass
class ConnectRequest:
    user_details: UserObject = field(metadata=config(field_name="user_details"))
    device: Optional[DeviceFields] = field(
        metadata=config(field_name="device"), default=None
    )
