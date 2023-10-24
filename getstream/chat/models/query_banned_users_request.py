# THIS FILE IS GENERATED FROM github.com/GetStream/protocol/tree/main/openapi-gen/templates/python/type.tmpl
from dataclasses import dataclass, field
from dataclasses_json import config, dataclass_json

from typing import Dict, List, Optional
from datetime import datetime
from dateutil.parser import parse
from marshmallow import fields
from getstream.chat.models.user_object import UserObject
from getstream.chat.models.sort_param import SortParam


@dataclass_json
@dataclass
class QueryBannedUsersRequest:
    filter_conditions: Dict[str, object] = field(
        metadata=config(field_name="filter_conditions")
    )
    offset: Optional[int] = field(metadata=config(field_name="offset"), default=None)
    user: Optional[UserObject] = field(metadata=config(field_name="user"), default=None)
    user_id: Optional[str] = field(metadata=config(field_name="user_id"), default=None)
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
    created_at_before_or_equal: Optional[datetime] = field(
        metadata=config(
            field_name="created_at_before_or_equal",
            encoder=lambda d: d.isoformat() if d is not None else None,
            decoder=parse,
            mm_field=fields.DateTime(format="iso"),
        ),
        default=None,
    )
    limit: Optional[int] = field(metadata=config(field_name="limit"), default=None)
    sort: Optional[List[SortParam]] = field(
        metadata=config(field_name="sort"), default=None
    )
    created_at_after: Optional[datetime] = field(
        metadata=config(
            field_name="created_at_after",
            encoder=lambda d: d.isoformat() if d is not None else None,
            decoder=parse,
            mm_field=fields.DateTime(format="iso"),
        ),
        default=None,
    )
