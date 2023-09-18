from dataclasses import dataclass, field
from dataclasses_json import config, dataclass_json

from typing import List, Optional


@dataclass_json
@dataclass
class GeofenceSettingsRequest:
    names: Optional[List[str]] = field(
        metadata=config(field_name="names"), default=None
    )
