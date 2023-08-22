from dataclasses import dataclass
from typing import Optional, Dict, List

from models.model_sort_param_request import SortParamRequest


@dataclass
class QueryMembersRequest:
    filter_conditions: Optional[Dict[str, object]] = None
    id: str
    limit: Optional[int] = None
    next: Optional[str] = None
    prev: Optional[str] = None
    sort: Optional[List[SortParamRequest]] = None
    type: str
