from dataclasses import dataclass, field
from dataclasses_json import config, dataclass_json

from typing import List, Dict, Optional
from datetime import datetime
from getstream.models.user_response import UserResponse
from getstream.models.egress_response import EgressResponse
from getstream.models.call_session_response import CallSessionResponse
from getstream.models.call_settings_response import CallSettingsResponse
from getstream.models.call_ingress_response import CallIngressResponse


@dataclass_json
@dataclass
class CallResponse:
    cid: str = field(metadata=config(field_name="cid"))
    current_session_id: str = field(metadata=config(field_name="current_session_id"))
    id: str = field(metadata=config(field_name="id"))
    ingress: CallIngressResponse = field(metadata=config(field_name="ingress"))
    backstage: bool = field(metadata=config(field_name="backstage"))
    created_by: UserResponse = field(metadata=config(field_name="created_by"))
    egress: EgressResponse = field(metadata=config(field_name="egress"))
    type: str = field(metadata=config(field_name="type"))
    updated_at: datetime = field(metadata=config(field_name="updated_at"))
    created_at: datetime = field(metadata=config(field_name="created_at"))
    settings: CallSettingsResponse = field(metadata=config(field_name="settings"))
    recording: bool = field(metadata=config(field_name="recording"))
    custom: Dict[str, object] = field(metadata=config(field_name="custom"))
    transcribing: bool = field(metadata=config(field_name="transcribing"))
    blocked_user_ids: List[str] = field(metadata=config(field_name="blocked_user_ids"))
    starts_at: Optional[datetime] = field(
        metadata=config(field_name="starts_at"), default=None
    )
    session: Optional[CallSessionResponse] = field(
        metadata=config(field_name="session"), default=None
    )
    ended_at: Optional[datetime] = field(
        metadata=config(field_name="ended_at"), default=None
    )
    team: Optional[str] = field(metadata=config(field_name="team"), default=None)
