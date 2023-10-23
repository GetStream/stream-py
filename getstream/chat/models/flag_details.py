# THIS FILE IS GENERATED FROM github.com/GetStream/protocol/tree/main/openapi-gen/templates/python/type.tmpl
from dataclasses import dataclass, field
from dataclasses_json import config, dataclass_json

from typing import Optional
from getstream.chat.models.automod_details import AutomodDetails


@dataclass_json
@dataclass
class FlagDetails:
    automod: Optional[AutomodDetails] = field(
        metadata=config(field_name="automod"), default=None
    )
