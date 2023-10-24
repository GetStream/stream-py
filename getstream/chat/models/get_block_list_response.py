# THIS FILE IS GENERATED FROM github.com/GetStream/protocol/tree/main/openapi-gen/templates/python/type.tmpl
from dataclasses import dataclass, field
from dataclasses_json import config, dataclass_json

from typing import Optional
from getstream.chat.models.block_list import BlockList


@dataclass_json
@dataclass
class GetBlockListResponse:
    duration: str = field(metadata=config(field_name="duration"))
    blocklist: Optional[BlockList] = field(
        metadata=config(field_name="blocklist"), default=None
    )
