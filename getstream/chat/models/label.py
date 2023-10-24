# THIS FILE IS GENERATED FROM github.com/GetStream/protocol/tree/main/openapi-gen/templates/python/type.tmpl
from dataclasses import dataclass, field
from dataclasses_json import config, dataclass_json

from typing import List, Optional


@dataclass_json
@dataclass
class Label:
    name: str = field(metadata=config(field_name="name"))
    phrase_list_ids: Optional[List[int]] = field(
        metadata=config(field_name="phrase_list_ids"), default=None
    )
