from dataclasses import dataclass, field
from dataclasses_json import config, dataclass_json

from typing import Optional


@dataclass_json
@dataclass
class ScreensharingSettingsRequest:
    enabled: Optional[bool] = field(metadata=config(field_name="enabled"), default=None)
    access_request_enabled: Optional[bool] = field(
        metadata=config(field_name="access_request_enabled"), default=None
    )
