from dataclasses import dataclass, field
from typing import Optional
from dataclasses_json import config, dataclass_json


@dataclass_json
@dataclass
class BackstageSettingsRequest:
    enabled: Optional[bool] = field(metadata=config(field_name="enabled"), default=None)
