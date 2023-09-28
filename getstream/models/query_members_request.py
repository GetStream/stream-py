from dataclasses import dataclass, field
from dataclasses_json import config, dataclass_json

from typing import List, Dict, Optional
from getstream.models.sort_param_request import SortParamRequest


@dataclass_json
@dataclass
class QueryMembersRequest:
    id: str = field(metadata=config(field_name="id"))
    type: str = field(metadata=config(field_name="type"))
    limit: Optional[int] = field(metadata=config(field_name="limit"), default=None)
    next: Optional[str] = field(metadata=config(field_name="next"), default=None)
    prev: Optional[str] = field(metadata=config(field_name="prev"), default=None)
    sort: Optional[List[SortParamRequest]] = field(
        metadata=config(field_name="sort"), default=None
    )
    filter_conditions: Optional[Dict[str, object]] = field(
        metadata=config(field_name="filter_conditions"), default=None
    )
