# THIS FILE IS GENERATED FROM github.com/GetStream/protocol/tree/main/openapi-gen/templates/python/type.tmpl
from dataclasses import dataclass, field
from dataclasses_json import config, dataclass_json

from typing import List, Optional
from getstream.models.sort_param_request import SortParamRequest


@dataclass_json
@dataclass
class QueryMembersRequest:
    type: str = field(metadata=config(field_name="type"))
    id: str = field(metadata=config(field_name="id"))
    prev: Optional[str] = field(metadata=config(field_name="prev"), default=None)
    sort: Optional[List[SortParamRequest]] = field(
        metadata=config(field_name="sort"), default=None
    )
    filter_conditions: Optional[object] = field(
        metadata=config(field_name="filter_conditions"), default=None
    )
    limit: Optional[int] = field(metadata=config(field_name="limit"), default=None)
    next: Optional[str] = field(metadata=config(field_name="next"), default=None)
