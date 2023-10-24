# THIS FILE IS GENERATED FROM github.com/GetStream/protocol/tree/main/openapi-gen/templates/python/type.tmpl
from dataclasses import dataclass, field
from dataclasses_json import config, dataclass_json

from typing import Dict, List, Optional
from getstream.chat.models.sort_param import SortParam


@dataclass_json
@dataclass
class SearchRequest:
    filter_conditions: Dict[str, object] = field(
        metadata=config(field_name="filter_conditions")
    )
    limit: Optional[int] = field(metadata=config(field_name="limit"), default=None)
    message_filter_conditions: Optional[Dict[str, object]] = field(
        metadata=config(field_name="message_filter_conditions"), default=None
    )
    next: Optional[str] = field(metadata=config(field_name="next"), default=None)
    offset: Optional[int] = field(metadata=config(field_name="offset"), default=None)
    query: Optional[str] = field(metadata=config(field_name="query"), default=None)
    sort: Optional[List[SortParam]] = field(
        metadata=config(field_name="sort"), default=None
    )
