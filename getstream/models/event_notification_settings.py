# THIS FILE IS GENERATED FROM github.com/GetStream/protocol/tree/main/openapi-gen/templates/python/type.tmpl
from dataclasses import dataclass, field
from dataclasses_json import config, dataclass_json

from getstream.models.apns import Apns


@dataclass_json
@dataclass
class EventNotificationSettings:
    apns: Apns = field(metadata=config(field_name="apns"))
    enabled: bool = field(metadata=config(field_name="enabled"))
