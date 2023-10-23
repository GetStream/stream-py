# THIS FILE IS GENERATED FROM github.com/GetStream/protocol/tree/main/openapi-gen/templates/python/type.tmpl
from dataclasses import dataclass, field
from dataclasses_json import config, dataclass_json

from typing import Optional
from getstream.chat.models.flag import Flag


@dataclass_json
@dataclass
class FlagResponse:
    duration: str = field(metadata=config(field_name="duration"))
    flag: Optional[Flag] = field(metadata=config(field_name="flag"), default=None)
