# THIS FILE IS GENERATED FROM github.com/GetStream/protocol/tree/main/openapi-gen/templates/python/type.tmpl
from dataclasses import dataclass, field
from dataclasses_json import config, dataclass_json

from typing import Optional
from getstream.models.apns_request import Apnsrequest


@dataclass_json
@dataclass
class EventNotificationSettingsRequest:
    apns: Optional[Apnsrequest] = field(
        metadata=config(field_name="apns"), default=None
    )
    enabled: Optional[bool] = field(metadata=config(field_name="enabled"), default=None)
