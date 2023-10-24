# THIS FILE IS GENERATED FROM github.com/GetStream/protocol/tree/main/openapi-gen/templates/python/type.tmpl
from dataclasses import dataclass, field
from dataclasses_json import config, dataclass_json

from typing import Optional
from getstream.chat.models.search_result_message import SearchResultMessage


@dataclass_json
@dataclass
class SearchResult:
    message: Optional[SearchResultMessage] = field(
        metadata=config(field_name="message"), default=None
    )
