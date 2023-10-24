# THIS FILE IS GENERATED FROM github.com/GetStream/protocol/tree/main/openapi-gen/templates/python/type.tmpl
from dataclasses import dataclass, field
from dataclasses_json import config, dataclass_json

from typing import List, Optional


@dataclass_json
@dataclass
class DeleteChannelsRequest:
    hard_delete: Optional[bool] = field(
        metadata=config(field_name="hard_delete"), default=None
    )
    cids: Optional[List[str]] = field(metadata=config(field_name="cids"), default=None)
