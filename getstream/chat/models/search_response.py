# THIS FILE IS GENERATED FROM github.com/GetStream/protocol/tree/main/openapi-gen/templates/python/type.tmpl
from dataclasses import dataclass, field
from dataclasses_json import config, dataclass_json

from typing import List, Optional
from getstream.chat.models.search_result import SearchResult
from getstream.chat.models.search_warning import SearchWarning


@dataclass_json
@dataclass
class SearchResponse:
    duration: str = field(metadata=config(field_name="duration"))
    results: List[SearchResult] = field(metadata=config(field_name="results"))
    next: Optional[str] = field(metadata=config(field_name="next"), default=None)
    previous: Optional[str] = field(
        metadata=config(field_name="previous"), default=None
    )
    results_warning: Optional[SearchWarning] = field(
        metadata=config(field_name="results_warning"), default=None
    )
