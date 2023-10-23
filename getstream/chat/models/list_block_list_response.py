# THIS FILE IS GENERATED FROM github.com/GetStream/protocol/tree/main/openapi-gen/templates/python/type.tmpl
from dataclasses import dataclass, field
from dataclasses_json import config, dataclass_json

from typing import List
from getstream.chat.models.block_list import BlockList


@dataclass_json
@dataclass
class ListBlockListResponse:
    blocklists: List[BlockList] = field(metadata=config(field_name="blocklists"))
    duration: str = field(metadata=config(field_name="duration"))
