from dataclasses import dataclass, field
from dataclasses_json import config, dataclass_json

from typing import List, Optional
from getstream.models.member_request import MemberRequest


@dataclass_json
@dataclass
class UpdateCallMembersRequest:
    update_members: Optional[List[MemberRequest]] = field(
        metadata=config(field_name="update_members"), default=None
    )
    remove_members: Optional[List[str]] = field(
        metadata=config(field_name="remove_members"), default=None
    )
