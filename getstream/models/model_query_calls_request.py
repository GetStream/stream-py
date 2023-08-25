from dataclasses import dataclass, field
from typing import Dict, Optional, List

from .model_sort_param_request import SortParamRequest


@dataclass
class QueryCallsRequest:
    FilterConditions: Optional[Dict[str, object]] = field(default_factory=dict)
    Limit: Optional[int] = None
    Next: Optional[str] = None
    Prev: Optional[str] = None
    Sort: Optional[List[SortParamRequest]] = field(default_factory=list)
    Watch: Optional[bool] = None
