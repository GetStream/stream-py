from dataclasses import dataclass, field
from typing import Dict, Optional, List

from .model_sort_param_request import SortParamRequest


@dataclass
class QueryCallsRequest:
    filter_conditions: Optional[Dict[str, object]] = field(default_factory=dict)
    limit: Optional[int] = None
    next: Optional[str] = None
    prev: Optional[str] = None
    sort: Optional[List[SortParamRequest]] = field(default_factory=list)
    watch: Optional[bool] = None

    @classmethod
    def from_dict(cls, data: dict) -> "QueryCallsRequest":
        if data.get("sort"):
            data["sort"] = [SortParamRequest.from_dict(d) for d in data["sort"]]
        return cls(**data)
