# THIS FILE IS GENERATED FROM github.com/GetStream/protocol/tree/main/openapi-gen/templates/python/type.tmpl
from dataclasses import dataclass, field
from dataclasses_json import config, dataclass_json

from typing import List, Optional
from datetime import datetime
from dateutil.parser import parse
from marshmallow import fields
from getstream.chat.models.import_task_history import ImportTaskHistory


@dataclass_json
@dataclass
class ImportTask:
    path: str = field(metadata=config(field_name="path"))
    state: str = field(metadata=config(field_name="state"))
    updated_at: datetime = field(
        metadata=config(
            field_name="updated_at",
            encoder=lambda d: d.isoformat(),
            decoder=parse,
            mm_field=fields.DateTime(format="iso"),
        )
    )
    created_at: datetime = field(
        metadata=config(
            field_name="created_at",
            encoder=lambda d: d.isoformat(),
            decoder=parse,
            mm_field=fields.DateTime(format="iso"),
        )
    )
    id: str = field(metadata=config(field_name="id"))
    history: List[ImportTaskHistory] = field(metadata=config(field_name="history"))
    mode: str = field(metadata=config(field_name="mode"))
    result: Optional[object] = field(metadata=config(field_name="result"), default=None)
    size: Optional[int] = field(metadata=config(field_name="size"), default=None)
