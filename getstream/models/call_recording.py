from dataclasses import dataclass, field
from dataclasses_json import config, dataclass_json

from datetime import datetime
from marshmallow import fields


@dataclass_json
@dataclass
class CallRecording:
    end_time: datetime = field(
        metadata=config(
            field_name="end_time",
            encoder=datetime.isoformat,
            decoder=datetime.fromisoformat,
            mm_field=fields.DateTime(format="iso"),
        )
    )
    filename: str = field(metadata=config(field_name="filename"))
    start_time: datetime = field(
        metadata=config(
            field_name="start_time",
            encoder=datetime.isoformat,
            decoder=datetime.fromisoformat,
            mm_field=fields.DateTime(format="iso"),
        )
    )
    url: str = field(metadata=config(field_name="url"))
