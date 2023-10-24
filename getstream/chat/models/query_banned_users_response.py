# THIS FILE IS GENERATED FROM github.com/GetStream/protocol/tree/main/openapi-gen/templates/python/type.tmpl
from dataclasses import dataclass, field
from dataclasses_json import config, dataclass_json

from typing import List
from getstream.chat.models.ban_response import BanResponse


@dataclass_json
@dataclass
class QueryBannedUsersResponse:
    bans: List[BanResponse] = field(metadata=config(field_name="bans"))
    duration: str = field(metadata=config(field_name="duration"))
