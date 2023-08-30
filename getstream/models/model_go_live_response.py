from dataclasses import dataclass

from .model_call_response import CallResponse


@dataclass
class GoLiveResponse:
    call: CallResponse
    duration: str

    @classmethod
    def from_dict(cls, data: dict) -> "GoLiveResponse":
        data["call"] = CallResponse.from_dict(data["call"])
        return cls(**data)
