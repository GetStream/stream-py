# THIS FILE IS GENERATED FROM github.com/GetStream/protocol/tree/main/openapi-gen/templates/python/type.tmpl
from dataclasses import dataclass, field
from dataclasses_json import config, dataclass_json

from typing import List
from datetime import datetime
from dateutil.parser import parse
from marshmallow import fields
from getstream.chat.models.label import Label


@dataclass_json
@dataclass
class FlagFeedback:
    message_id: str = field(metadata=config(field_name="message_id"))
    created_at: datetime = field(
        metadata=config(
            field_name="created_at",
            encoder=lambda d: d.isoformat(),
            decoder=parse,
            mm_field=fields.DateTime(format="iso"),
        )
    )
    labels: List[Label] = field(metadata=config(field_name="labels"))
