# THIS FILE IS GENERATED FROM github.com/GetStream/protocol/tree/main/openapi-gen/templates/python/type.tmpl
from dataclasses import dataclass, field
from dataclasses_json import config, dataclass_json

from typing import List, Optional
from getstream.models.member_request import MemberRequest


@dataclass_json
@dataclass
class UpdateCallMembersRequest:
    remove_members: Optional[List[str]] = field(
        metadata=config(field_name="remove_members"), default=None
    )
    update_members: Optional[List[MemberRequest]] = field(
        metadata=config(field_name="update_members"), default=None
    )
