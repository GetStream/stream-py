# THIS FILE IS GENERATED FROM github.com/GetStream/protocol/tree/main/openapi-gen/templates/python/type.tmpl
from dataclasses import dataclass, field
from dataclasses_json import config, dataclass_json

from typing import List, Optional


@dataclass_json
@dataclass
class SearchWarning:
    warning_code: int = field(metadata=config(field_name="warning_code"))
    warning_description: str = field(metadata=config(field_name="warning_description"))
    channel_search_count: Optional[int] = field(
        metadata=config(field_name="channel_search_count"), default=None
    )
    channel_search_cids: Optional[List[str]] = field(
        metadata=config(field_name="channel_search_cids"), default=None
    )
