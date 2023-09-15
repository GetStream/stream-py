from dataclasses import dataclass, field

from dataclasses_json import config, dataclass_json
from call_response import CallResponse
from member_response import MemberResponse


@dataclass_json
@dataclass
class CallMemberUpdatedPermissionEvent:
    created_at: str = field(metadata=config(field_name="created_at"))
    members: list[MemberResponse] = field(metadata=config(field_name="members"))
    type: str = field(metadata=config(field_name="type"))
    call: CallResponse = field(metadata=config(field_name="call"))
    call_cid: str = field(metadata=config(field_name="call_cid"))
    capabilities_by_role: dict[str, list[str]] = field(
        metadata=config(field_name="capabilities_by_role")
    )
