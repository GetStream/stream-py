# THIS FILE IS GENERATED FROM github.com/GetStream/protocol/tree/main/openapi-gen/templates/python/type.tmpl
from dataclasses import dataclass, field
from dataclasses_json import config, dataclass_json

from typing import Optional
from getstream.chat.models.user_object_request import UserObjectRequest


@dataclass_json
@dataclass
class CheckPushRequest:
    firebase_template: Optional[str] = field(
        metadata=config(field_name="firebase_template"), default=None
    )
    user: Optional[UserObjectRequest] = field(
        metadata=config(field_name="user"), default=None
    )
    apn_template: Optional[str] = field(
        metadata=config(field_name="apn_template"), default=None
    )
    firebase_data_template: Optional[str] = field(
        metadata=config(field_name="firebase_data_template"), default=None
    )
    message_id: Optional[str] = field(
        metadata=config(field_name="message_id"), default=None
    )
    push_provider_name: Optional[str] = field(
        metadata=config(field_name="push_provider_name"), default=None
    )
    push_provider_type: Optional[str] = field(
        metadata=config(field_name="push_provider_type"), default=None
    )
    skip_devices: Optional[bool] = field(
        metadata=config(field_name="skip_devices"), default=None
    )
    user_id: Optional[str] = field(metadata=config(field_name="user_id"), default=None)
