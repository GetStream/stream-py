# THIS FILE IS GENERATED FROM github.com/GetStream/protocol/tree/main/openapi-gen/templates/python/type.tmpl
from dataclasses import dataclass, field
from dataclasses_json import config, dataclass_json

from typing import List, Optional
from datetime import datetime
from dateutil.parser import parse
from marshmallow import fields
from getstream.chat.models.user_object_request import UserObjectRequest


@dataclass_json
@dataclass
class SyncRequest:
    last_sync_at: datetime = field(
        metadata=config(
            field_name="last_sync_at",
            encoder=lambda d: d.isoformat(),
            decoder=parse,
            mm_field=fields.DateTime(format="iso"),
        )
    )
    with_inaccessible_cids: Optional[bool] = field(
        metadata=config(field_name="with_inaccessible_cids"), default=None
    )
    channel_cids: Optional[List[str]] = field(
        metadata=config(field_name="channel_cids"), default=None
    )
    client_id: Optional[str] = field(
        metadata=config(field_name="client_id"), default=None
    )
    connection_id: Optional[str] = field(
        metadata=config(field_name="connection_id"), default=None
    )
    user: Optional[UserObjectRequest] = field(
        metadata=config(field_name="user"), default=None
    )
    user_id: Optional[str] = field(metadata=config(field_name="user_id"), default=None)
    watch: Optional[bool] = field(metadata=config(field_name="watch"), default=None)
