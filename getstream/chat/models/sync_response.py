# THIS FILE IS GENERATED FROM github.com/GetStream/protocol/tree/main/openapi-gen/templates/python/type.tmpl
from dataclasses import dataclass, field
from dataclasses_json import config, dataclass_json

from typing import List, Optional
from getstream.chat.models.event import Event


@dataclass_json
@dataclass
class SyncResponse:
    duration: str = field(metadata=config(field_name="duration"))
    events: List[Event] = field(metadata=config(field_name="events"))
    inaccessible_cids: Optional[List[str]] = field(
        metadata=config(field_name="inaccessible_cids"), default=None
    )
