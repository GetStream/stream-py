from dataclasses import dataclass, field
from dataclasses_json import config, dataclass_json

from datetime import datetime
from getstream.models.api_error import Apierror


@dataclass_json
@dataclass
class ConnectionErrorEvent:
    type: str = field(metadata=config(field_name="type"))
    connection_id: str = field(metadata=config(field_name="connection_id"))
    created_at: datetime = field(metadata=config(field_name="created_at"))
    error: Apierror = field(metadata=config(field_name="error"))
