from dataclasses import dataclass, field
from typing import Optional
from dataclasses_json import config, dataclass_json
from apns_request import Apnsrequest


@dataclass_json
@dataclass
class EventNotificationSettingsRequest:
    enabled: Optional[bool] = field(metadata=config(field_name="enabled"), default=None)
    apns: Optional[Apnsrequest] = field(
        metadata=config(field_name="apns"), default=None
    )
