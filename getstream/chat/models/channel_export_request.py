# THIS FILE IS GENERATED FROM github.com/GetStream/protocol/tree/main/openapi-gen/templates/python/type.tmpl
from dataclasses import dataclass, field
from dataclasses_json import config, dataclass_json

from typing import Optional
from datetime import datetime
from dateutil.parser import parse
from marshmallow import fields


@dataclass_json
@dataclass
class ChannelExportRequest:
    messages_until: Optional[datetime] = field(
        metadata=config(
            field_name="messages_until",
            encoder=lambda d: d.isoformat() if d is not None else None,
            decoder=parse,
            mm_field=fields.DateTime(format="iso"),
        ),
        default=None,
    )
    type: Optional[str] = field(metadata=config(field_name="type"), default=None)
    cid: Optional[str] = field(metadata=config(field_name="cid"), default=None)
    id: Optional[str] = field(metadata=config(field_name="id"), default=None)
    messages_since: Optional[datetime] = field(
        metadata=config(
            field_name="messages_since",
            encoder=lambda d: d.isoformat() if d is not None else None,
            decoder=parse,
            mm_field=fields.DateTime(format="iso"),
        ),
        default=None,
    )
