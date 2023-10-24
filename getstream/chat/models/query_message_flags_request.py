# THIS FILE IS GENERATED FROM github.com/GetStream/protocol/tree/main/openapi-gen/templates/python/type.tmpl
from dataclasses import dataclass, field
from dataclasses_json import config, dataclass_json

from typing import Dict, Optional
from getstream.chat.models.user_object import UserObject


@dataclass_json
@dataclass
class QueryMessageFlagsRequest:
    filter_conditions: Optional[Dict[str, object]] = field(
        metadata=config(field_name="filter_conditions"), default=None
    )
    limit: Optional[int] = field(metadata=config(field_name="limit"), default=None)
    offset: Optional[int] = field(metadata=config(field_name="offset"), default=None)
    user: Optional[UserObject] = field(metadata=config(field_name="user"), default=None)
    user_id: Optional[str] = field(metadata=config(field_name="user_id"), default=None)
