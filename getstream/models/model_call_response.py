from dataclasses import dataclass
from typing import Optional, List, Dict, Any
import datetime
from models.model_call_ingress_response import CallIngressResponse

from models.model_call_ring_event import UserResponse
from models.model_call_session_response import CallSessionResponse
from models.model_call_settings_response import CallSettingsResponse
from models.model_egress_response import EgressResponse


@dataclass
class CallResponse:
    backstage: bool
    blocked_user_ids: List[str]
    cid: str
    created_at: datetime.datetime
    created_by: UserResponse
    current_session_id: str
    custom: Dict[str, Any]
    egress: EgressResponse
    ended_at: Optional[datetime.datetime]
    id: str
    ingress: CallIngressResponse
    recording: bool
    session: Optional[CallSessionResponse]
    settings: CallSettingsResponse
    starts_at: Optional[datetime.datetime]
    team: Optional[str]
    transcribing: bool
    type: str
    updated_at: datetime.datetime
