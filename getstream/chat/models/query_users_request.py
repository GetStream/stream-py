# THIS FILE IS GENERATED FROM github.com/GetStream/protocol/tree/main/openapi-gen/templates/python/type.tmpl
from dataclasses import dataclass, field
from dataclasses_json import config, dataclass_json

from typing import List, Dict, Optional
from getstream.chat.models.user_object import UserObject
from getstream.chat.models.sort_param import SortParam


@dataclass_json
@dataclass
class QueryUsersRequest:
    filter_conditions: Dict[str, object] = field(
        metadata=config(field_name="filter_conditions")
    )
    sort: List[SortParam] = field(metadata=config(field_name="sort"))
    user_id: Optional[str] = field(metadata=config(field_name="user_id"), default=None)
    id_gt: Optional[str] = field(metadata=config(field_name="id_gt"), default=None)
    id_gte: Optional[str] = field(metadata=config(field_name="id_gte"), default=None)
    presence: Optional[bool] = field(
        metadata=config(field_name="presence"), default=None
    )
    user: Optional[UserObject] = field(metadata=config(field_name="user"), default=None)
    offset: Optional[int] = field(metadata=config(field_name="offset"), default=None)
    client_id: Optional[str] = field(
        metadata=config(field_name="client_id"), default=None
    )
    connection_id: Optional[str] = field(
        metadata=config(field_name="connection_id"), default=None
    )
    id_lt: Optional[str] = field(metadata=config(field_name="id_lt"), default=None)
    id_lte: Optional[str] = field(metadata=config(field_name="id_lte"), default=None)
    limit: Optional[int] = field(metadata=config(field_name="limit"), default=None)
