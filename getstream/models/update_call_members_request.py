from dataclasses import dataclass, field

from dataclasses_json import config, dataclass_json
from member_request import MemberRequest


@dataclass_json
@dataclass
class UpdateCallMembersRequest:
    remove_members: Optional[list[str]] = field(
        metadata=config(field_name="remove_members"), default=None
    )
    update_members: Optional[list[MemberRequest]] = field(
        metadata=config(field_name="update_members"), default=None
    )
