from dataclasses import dataclass, field

from dataclasses_json import config, dataclass_json


@dataclass_json
@dataclass
class GeofenceSettingsRequest:
    names: Optional[list[str]] = field(
        metadata=config(field_name="names"), default=None
    )
