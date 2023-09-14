from dataclasses import dataclass, field
from typing import Optional
from dataclasses_json import config, dataclass_json


@dataclass_json
@dataclass
class ScreensharingSettings:
    access_request_enabled: bool = field(
        metadata=config(field_name="access_request_enabled")
    )
    enabled: bool = field(metadata=config(field_name="enabled"))
