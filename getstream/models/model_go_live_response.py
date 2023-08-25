from dataclasses import dataclass

from .model_call_response import CallResponse


@dataclass
class GoLiveResponse:
    call: CallResponse
    duration: str
