from dataclasses import dataclass, field
from dataclasses_json import config, dataclass_json

from typing import Optional


@dataclass_json
@dataclass
class BackstageSettingsRequest:
    enabled: Optional[bool] = field(metadata=config(field_name="enabled"), default=None)
