# THIS FILE IS GENERATED FROM github.com/GetStream/protocol/tree/main/openapi-gen/templates/python/type.tmpl
from dataclasses import dataclass, field
from dataclasses_json import config, dataclass_json

from typing import List, Dict
from datetime import datetime
from dateutil.parser import parse
from marshmallow import fields
from getstream.models.call_response import CallResponse


@dataclass_json
@dataclass
class CallUpdatedEvent:
    call: CallResponse = field(metadata=config(field_name="call"))
    call_cid: str = field(metadata=config(field_name="call_cid"))
    capabilities_by_role: Dict[str, List[str]] = field(
        metadata=config(field_name="capabilities_by_role")
    )
    created_at: datetime = field(
        metadata=config(
            field_name="created_at",
            encoder=lambda d: d.isoformat(),
            decoder=parse,
            mm_field=fields.DateTime(format="iso"),
        )
    )
    type: str = field(metadata=config(field_name="type"))
