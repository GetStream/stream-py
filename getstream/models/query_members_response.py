from dataclasses import dataclass, field

from dataclasses_json import config, dataclass_json
from member_response import MemberResponse


@dataclass_json
@dataclass
class QueryMembersResponse:
    duration: str = field(metadata=config(field_name="duration"))
    members: list[MemberResponse] = field(metadata=config(field_name="members"))
    prev: Optional[str] = field(metadata=config(field_name="prev"), default=None)
    next: Optional[str] = field(metadata=config(field_name="next"), default=None)
