from dataclasses import dataclass, field
from typing import Optional
from dataclasses_json import config, dataclass_json
from apns import Apns


@dataclass_json
@dataclass
class EventNotificationSettings:
    apns: Apns = field(metadata=config(field_name="apns"))
    enabled: bool = field(metadata=config(field_name="enabled"))
