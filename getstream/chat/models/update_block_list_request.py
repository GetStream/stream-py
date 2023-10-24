# THIS FILE IS GENERATED FROM github.com/GetStream/protocol/tree/main/openapi-gen/templates/python/type.tmpl
from dataclasses import dataclass, field
from dataclasses_json import config, dataclass_json

from typing import List, Optional


@dataclass_json
@dataclass
class UpdateBlockListRequest:
    name: Optional[str] = field(metadata=config(field_name="Name"), default=None)
    words: Optional[List[str]] = field(
        metadata=config(field_name="words"), default=None
    )
