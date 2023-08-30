from dataclasses import dataclass
from typing import Optional, List, Dict, Any
import datetime

from .model_user_response import UserResponse

from .model_call_ingress_response import CallIngressResponse
from .model_call_session_response import CallSessionResponse
from .model_call_settings_response import CallSettingsResponse
from .model_egress_response import EgressResponse


@dataclass
class CallResponse:
    id: str
    backstage: bool
    blocked_user_ids: List[str]
    cid: str
    created_at: datetime.datetime
    created_by: UserResponse
    current_session_id: str
    custom: Dict[str, Any]
    egress: EgressResponse
    ingress: CallIngressResponse
    recording: bool

    settings: CallSettingsResponse

    transcribing: bool
    type: str
    updated_at: datetime.datetime
    session: Optional[CallSessionResponse] = None
    starts_at: Optional[datetime.datetime] = None
    team: Optional[str] = None
    ended_at: Optional[datetime.datetime] = None

    @classmethod
    def from_dict(cls, data: dict) -> "CallResponse":
        data["settings"] = CallSettingsResponse.from_dict(data["settings"])
        data["created_by"] = UserResponse.from_dict(data["created_by"])
        data["egress"] = EgressResponse.from_dict(data["egress"])
        data["ingress"] = CallIngressResponse.from_dict(data["ingress"])
        if data.get("session"):
            data["session"] = CallSessionResponse.from_dict(data["session"])

        return cls(**data)
