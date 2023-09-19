from dataclasses import dataclass, field
from dataclasses_json import config, dataclass_json

from datetime import datetime
from marshmallow import fields
from getstream.models.api_error import Apierror


@dataclass_json
@dataclass
class ConnectionErrorEvent:
    connection_id: str = field(metadata=config(field_name="connection_id"))
    created_at: datetime = field(
        metadata=config(
            field_name="created_at",
            encoder=datetime.isoformat,
            decoder=datetime.fromisoformat,
            mm_field=fields.DateTime(format="iso"),
        )
    )
    error: Apierror = field(metadata=config(field_name="error"))
    type: str = field(metadata=config(field_name="type"))
