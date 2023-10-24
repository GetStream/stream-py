# THIS FILE IS GENERATED FROM github.com/GetStream/protocol/tree/main/openapi-gen/templates/python/type.tmpl
from dataclasses import dataclass, field
from dataclasses_json import config, dataclass_json

from datetime import datetime
from dateutil.parser import parse
from marshmallow import fields
from getstream.models.call_recording import CallRecording


@dataclass_json
@dataclass
class CallRecordingReadyEvent:
    call_cid: str = field(metadata=config(field_name="call_cid"))
    call_recording: CallRecording = field(metadata=config(field_name="call_recording"))
    created_at: datetime = field(
        metadata=config(
            field_name="created_at",
            encoder=lambda d: d.isoformat(),
            decoder=parse,
            mm_field=fields.DateTime(format="iso"),
        )
    )
    type: str = field(metadata=config(field_name="type"))
