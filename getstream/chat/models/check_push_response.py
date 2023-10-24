# THIS FILE IS GENERATED FROM github.com/GetStream/protocol/tree/main/openapi-gen/templates/python/type.tmpl
from dataclasses import dataclass, field
from dataclasses_json import config, dataclass_json

from typing import List, Dict, Optional
from getstream.chat.models.device_error_info import DeviceErrorInfo


@dataclass_json
@dataclass
class CheckPushResponse:
    duration: str = field(metadata=config(field_name="duration"))
    rendered_firebase_template: Optional[str] = field(
        metadata=config(field_name="rendered_firebase_template"), default=None
    )
    rendered_message: Optional[Dict[str, str]] = field(
        metadata=config(field_name="rendered_message"), default=None
    )
    skip_devices: Optional[bool] = field(
        metadata=config(field_name="skip_devices"), default=None
    )
    device_errors: Optional[Dict[str, DeviceErrorInfo]] = field(
        metadata=config(field_name="device_errors"), default=None
    )
    general_errors: Optional[List[str]] = field(
        metadata=config(field_name="general_errors"), default=None
    )
    rendered_apn_template: Optional[str] = field(
        metadata=config(field_name="rendered_apn_template"), default=None
    )
