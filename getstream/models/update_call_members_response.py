from dataclasses import dataclass, field
from dataclasses_json import config, dataclass_json

from typing import List
from getstream.models.member_response import MemberResponse


@dataclass_json
@dataclass
class UpdateCallMembersResponse:
    members: List[MemberResponse] = field(metadata=config(field_name="members"))
    duration: str = field(metadata=config(field_name="duration"))
