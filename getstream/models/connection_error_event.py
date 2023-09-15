from dataclasses import dataclass, field

from dataclasses_json import config, dataclass_json
from api_error import Apierror


@dataclass_json
@dataclass
class ConnectionErrorEvent:
    connection_id: str = field(metadata=config(field_name="connection_id"))
    created_at: str = field(metadata=config(field_name="created_at"))
    error: Apierror = field(metadata=config(field_name="error"))
    type: str = field(metadata=config(field_name="type"))
