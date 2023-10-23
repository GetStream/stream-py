# THIS FILE IS GENERATED FROM github.com/GetStream/protocol/tree/main/openapi-gen/templates/python/type.tmpl
from dataclasses import dataclass, field
from dataclasses_json import config, dataclass_json

from typing import Dict, Optional
from datetime import datetime
from dateutil.parser import parse
from marshmallow import fields
from getstream.chat.models.error_result import ErrorResult


@dataclass_json
@dataclass
class GetTaskResponse:
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
    duration: str = field(metadata=config(field_name="duration"))
    status: str = field(metadata=config(field_name="status"))
    task_id: str = field(metadata=config(field_name="task_id"))
    error: Optional[ErrorResult] = field(
        metadata=config(field_name="error"), default=None
    )
    result: Optional[Dict[str, object]] = field(
        metadata=config(field_name="result"), default=None
    )
