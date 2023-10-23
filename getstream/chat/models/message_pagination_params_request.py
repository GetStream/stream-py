# THIS FILE IS GENERATED FROM github.com/GetStream/protocol/tree/main/openapi-gen/templates/python/type.tmpl
from dataclasses import dataclass, field
from dataclasses_json import config, dataclass_json

from typing import Optional
from datetime import datetime
from dateutil.parser import parse
from marshmallow import fields


@dataclass_json
@dataclass
class MessagePaginationParamsRequest:
    id_gte: Optional[str] = field(metadata=config(field_name="id_gte"), default=None)
    id_lt: Optional[str] = field(metadata=config(field_name="id_lt"), default=None)
    limit: Optional[int] = field(metadata=config(field_name="limit"), default=None)
    created_at_around: Optional[datetime] = field(
        metadata=config(
            field_name="created_at_around",
            encoder=lambda d: d.isoformat() if d is not None else None,
            decoder=parse,
            mm_field=fields.DateTime(format="iso"),
        ),
        default=None,
    )
    created_at_before_or_equal: Optional[datetime] = field(
        metadata=config(
            field_name="created_at_before_or_equal",
            encoder=lambda d: d.isoformat() if d is not None else None,
            decoder=parse,
            mm_field=fields.DateTime(format="iso"),
        ),
        default=None,
    )
    id_around: Optional[str] = field(
        metadata=config(field_name="id_around"), default=None
    )
    id_gt: Optional[str] = field(metadata=config(field_name="id_gt"), default=None)
    offset: Optional[int] = field(metadata=config(field_name="offset"), default=None)
    created_at_after: Optional[datetime] = field(
        metadata=config(
            field_name="created_at_after",
            encoder=lambda d: d.isoformat() if d is not None else None,
            decoder=parse,
            mm_field=fields.DateTime(format="iso"),
        ),
        default=None,
    )
    created_at_after_or_equal: Optional[datetime] = field(
        metadata=config(
            field_name="created_at_after_or_equal",
            encoder=lambda d: d.isoformat() if d is not None else None,
            decoder=parse,
            mm_field=fields.DateTime(format="iso"),
        ),
        default=None,
    )
    created_at_before: Optional[datetime] = field(
        metadata=config(
            field_name="created_at_before",
            encoder=lambda d: d.isoformat() if d is not None else None,
            decoder=parse,
            mm_field=fields.DateTime(format="iso"),
        ),
        default=None,
    )
    id_lte: Optional[str] = field(metadata=config(field_name="id_lte"), default=None)
