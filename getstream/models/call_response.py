from dataclasses import dataclass, field
from typing import Optional
from dataclasses_json import config, dataclass_json
from user_response import UserResponse
from egress_response import EgressResponse
from call_session_response import CallSessionResponse
from call_ingress_response import CallIngressResponse
from call_settings_response import CallSettingsResponse


@dataclass_json
@dataclass
class CallResponse:
    transcribing: bool = field(metadata=config(field_name="transcribing"))
    cid: str = field(metadata=config(field_name="cid"))
    created_by: UserResponse = field(metadata=config(field_name="created_by"))
    current_session_id: str = field(metadata=config(field_name="current_session_id"))
    egress: EgressResponse = field(metadata=config(field_name="egress"))
    backstage: bool = field(metadata=config(field_name="backstage"))
    created_at: str = field(metadata=config(field_name="created_at"))
    id: str = field(metadata=config(field_name="id"))
    type: str = field(metadata=config(field_name="type"))
    blocked_user_ids: list[str] = field(metadata=config(field_name="blocked_user_ids"))
    updated_at: str = field(metadata=config(field_name="updated_at"))
    custom: dict[str, object] = field(metadata=config(field_name="custom"))
    ingress: CallIngressResponse = field(metadata=config(field_name="ingress"))
    recording: bool = field(metadata=config(field_name="recording"))
    settings: CallSettingsResponse = field(metadata=config(field_name="settings"))
    session: Optional[CallSessionResponse] = field(
        metadata=config(field_name="session"), default=None
    )
    team: Optional[str] = field(metadata=config(field_name="team"), default=None)
    ended_at: Optional[str] = field(
        metadata=config(field_name="ended_at"), default=None
    )
    starts_at: Optional[str] = field(
        metadata=config(field_name="starts_at"), default=None
    )
