# THIS FILE IS GENERATED FROM github.com/GetStream/protocol/tree/main/openapi-gen/templates/python/type.tmpl
from dataclasses import dataclass, field
from dataclasses_json import config, dataclass_json

from typing import List, Optional
from getstream.models.member_response import MemberResponse


@dataclass_json
@dataclass
class QueryMembersResponse:
    duration: str = field(metadata=config(field_name="duration"))
    members: List[MemberResponse] = field(metadata=config(field_name="members"))
    next: Optional[str] = field(metadata=config(field_name="next"), default=None)
    prev: Optional[str] = field(metadata=config(field_name="prev"), default=None)
