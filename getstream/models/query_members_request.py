from dataclasses import dataclass, field

from dataclasses_json import config, dataclass_json
from sort_param_request import SortParamRequest


@dataclass_json
@dataclass
class QueryMembersRequest:
    id: str = field(metadata=config(field_name="id"))
    type: str = field(metadata=config(field_name="type"))
    filter_conditions: Optional[dict[str, object]] = field(
        metadata=config(field_name="filter_conditions"), default=None
    )
    limit: Optional[int] = field(metadata=config(field_name="limit"), default=None)
    next: Optional[str] = field(metadata=config(field_name="next"), default=None)
    prev: Optional[str] = field(metadata=config(field_name="prev"), default=None)
    sort: Optional[list[SortParamRequest]] = field(
        metadata=config(field_name="sort"), default=None
    )
