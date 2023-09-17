from dataclasses import dataclass, field
from typing import Optional
from dataclasses_json import config, dataclass_json
from hls_settings_request import HlssettingsRequest


@dataclass_json
@dataclass
class BroadcastSettingsRequest:
    enabled: Optional[bool] = field(metadata=config(field_name="enabled"), default=None)
    hls: Optional[HlssettingsRequest] = field(
        metadata=config(field_name="hls"), default=None
    )
