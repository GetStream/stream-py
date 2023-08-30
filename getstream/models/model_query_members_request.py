from dataclasses import dataclass
from typing import Optional, Dict, List

from .model_sort_param_request import SortParamRequest


@dataclass
class QueryMembersRequest:
    id: str

    type: str
    limit: Optional[int] = None
    next: Optional[str] = None
    prev: Optional[str] = None
    sort: Optional[List[SortParamRequest]] = None
    filter_conditions: Optional[Dict[str, object]] = None

    @classmethod
    def from_dict(cls, data: dict) -> "QueryMembersRequest":
        if data.get("sort"):
            data["sort"] = [SortParamRequest.from_dict(d) for d in data["sort"]]
        return cls(**data)
