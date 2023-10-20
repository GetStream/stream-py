# THIS FILE IS GENERATED FROM github.com/GetStream/protocol/tree/main/openapi-gen/templates/python/type.tmpl
from dataclasses import dataclass, field
from dataclasses_json import config, dataclass_json

from typing import List, Optional
from getstream.models.member_response import MemberResponse
from getstream.models.own_capability import OwnCapability
from getstream.models.call_response import CallResponse
from getstream.models.credentials import Credentials


@dataclass_json
@dataclass
class JoinCallResponse:
    call: CallResponse = field(metadata=config(field_name="call"))
    created: bool = field(metadata=config(field_name="created"))
    credentials: Credentials = field(metadata=config(field_name="credentials"))
    duration: str = field(metadata=config(field_name="duration"))
    members: List[MemberResponse] = field(metadata=config(field_name="members"))
    own_capabilities: List[OwnCapability] = field(
        metadata=config(field_name="own_capabilities")
    )
    membership: Optional[MemberResponse] = field(
        metadata=config(field_name="membership"), default=None
    )
