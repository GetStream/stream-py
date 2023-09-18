from dataclasses import dataclass, field
from dataclasses_json import config, dataclass_json

from datetime import datetime
from getstream.models.own_user_response import OwnUserResponse


@dataclass_json
@dataclass
class ConnectedEvent:
    connection_id: str = field(metadata=config(field_name="connection_id"))
    created_at: datetime = field(metadata=config(field_name="created_at"))
    me: OwnUserResponse = field(metadata=config(field_name="me"))
    type: str = field(metadata=config(field_name="type"))
