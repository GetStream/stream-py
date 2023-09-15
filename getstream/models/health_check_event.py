from dataclasses import dataclass, field

from dataclasses_json import config, dataclass_json


@dataclass_json
@dataclass
class HealthCheckEvent:
    connection_id: str = field(metadata=config(field_name="connection_id"))
    created_at: str = field(metadata=config(field_name="created_at"))
    type: str = field(metadata=config(field_name="type"))
