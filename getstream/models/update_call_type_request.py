from dataclasses import dataclass, field
from dataclasses_json import config, dataclass_json

from typing import List, Dict, Optional
from getstream.models.notification_settings_request import NotificationSettingsRequest
from getstream.models.call_settings_request import CallSettingsRequest
from getstream.models.own_capability import OwnCapability


@dataclass_json
@dataclass
class UpdateCallTypeRequest:
    grants: Dict[str, List[OwnCapability]] = field(
        metadata=config(
            field_name="grants",
            encoder=lambda grants: {
                k: [OwnCapability.to_str(grant) for grant in v]
                for k, v in grants.items()
            },
            decoder=lambda grants: {
                k: [OwnCapability.from_str(grant) for grant in v]
                for k, v in grants.items()
            },
        )
    )
    notification_settings: Optional[NotificationSettingsRequest] = field(
        metadata=config(field_name="notification_settings"), default=None
    )
    settings: Optional[CallSettingsRequest] = field(
        metadata=config(field_name="settings"), default=None
    )
