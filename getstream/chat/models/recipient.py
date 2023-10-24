# THIS FILE IS GENERATED FROM github.com/GetStream/protocol/tree/main/openapi-gen/templates/python/type.tmpl
from dataclasses import dataclass, field
from dataclasses_json import config, dataclass_json

from datetime import datetime
from dateutil.parser import parse
from marshmallow import fields


@dataclass_json
@dataclass
class Recipient:
    receiver_id: str = field(metadata=config(field_name="receiver_id"))
    status: str = field(metadata=config(field_name="status"))
    updated_at: datetime = field(
        metadata=config(
            field_name="updated_at",
            encoder=lambda d: d.isoformat(),
            decoder=parse,
            mm_field=fields.DateTime(format="iso"),
        )
    )
    campaign_id: str = field(metadata=config(field_name="campaign_id"))
    channel_cid: str = field(metadata=config(field_name="channel_cid"))
    created_at: datetime = field(
        metadata=config(
            field_name="created_at",
            encoder=lambda d: d.isoformat(),
            decoder=parse,
            mm_field=fields.DateTime(format="iso"),
        )
    )
    details: str = field(metadata=config(field_name="details"))
    message_id: str = field(metadata=config(field_name="message_id"))
