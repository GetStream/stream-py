from dataclasses import dataclass

from .model_call_response import CallResponse


@dataclass
class StopLiveResponse:
    call: CallResponse
    duration: str

    @classmethod
    def from_dict(cls, data: dict) -> "StopLiveResponse":
        data["call"] = CallResponse.from_dict(data["call"])
        return cls(**data)
