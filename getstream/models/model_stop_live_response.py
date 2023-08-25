from dataclasses import dataclass

from .model_call_response import CallResponse


@dataclass
class StopLiveResponse:
    call: CallResponse
    duration: str
