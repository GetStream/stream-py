# THIS FILE IS GENERATED FROM github.com/GetStream/protocol/tree/main/openapi-gen/templates/python/type.tmpl
from dataclasses import dataclass, field
from dataclasses_json import config, dataclass_json

from typing import Optional
from datetime import datetime
from dateutil.parser import parse
from marshmallow import fields
from getstream.chat.models.error_result import ErrorResult
from getstream.chat.models.export_channels_result import ExportChannelsResult


@dataclass_json
@dataclass
class GetExportChannelsStatusResponse:
    duration: str = field(metadata=config(field_name="duration"))
    status: str = field(metadata=config(field_name="status"))
    task_id: str = field(metadata=config(field_name="task_id"))
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
    error: Optional[ErrorResult] = field(
        metadata=config(field_name="error"), default=None
    )
    result: Optional[ExportChannelsResult] = field(
        metadata=config(field_name="result"), default=None
    )
