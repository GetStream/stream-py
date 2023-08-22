from dataclasses import dataclass

from models.model_call_member_removed_event import CallResponse


@dataclass
class StopLiveResponse:
    call: CallResponse
    duration: str
