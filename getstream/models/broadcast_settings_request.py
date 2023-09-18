from dataclasses import dataclass, field
from dataclasses_json import config, dataclass_json

from typing import Optional
from getstream.models.hls_settings_request import HlssettingsRequest


@dataclass_json
@dataclass
class BroadcastSettingsRequest:
    hls: Optional[HlssettingsRequest] = field(
        metadata=config(field_name="hls"), default=None
    )
    enabled: Optional[bool] = field(metadata=config(field_name="enabled"), default=None)
