from dataclasses import dataclass
from typing import Dict

from .model_call_type_response import CallTypeResponse


@dataclass
class ListCallTypeResponse:
    call_types: Dict[str, CallTypeResponse]
    duration: str

    @classmethod
    def from_dict(cls, data: dict) -> "ListCallTypeResponse":
        data["call_types"] = {
            k: CallTypeResponse.from_dict(v) for k, v in data["call_types"].items()
        }
        return cls(**data)
