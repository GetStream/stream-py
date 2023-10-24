# THIS FILE IS GENERATED FROM github.com/GetStream/protocol/tree/main/openapi-gen/templates/python/type.tmpl
from dataclasses import dataclass, field
from dataclasses_json import config, dataclass_json

from typing import List
from getstream.chat.models.reaction import Reaction


@dataclass_json
@dataclass
class GetReactionsResponse:
    duration: str = field(metadata=config(field_name="duration"))
    reactions: List[Reaction] = field(metadata=config(field_name="reactions"))
