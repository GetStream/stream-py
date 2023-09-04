import dataclasses
from typing import List, Dict, Optional
from dataclasses import dataclass, field


def remap_fields(cls, data_dict: dict) -> dict:
    for field_ in dataclasses.fields(cls):
        serializedName = field_.metadata.get("serializedName")
        if serializedName and serializedName in data_dict:
            data_dict[field_.name] = data_dict.pop(serializedName)
    return data_dict


@dataclass
class APIError:
    status_code: int = field(metadata={"serializedName": "StatusCode"})
    code: int
    details: List[int]
    duration: str
    message: str
    more_info: str
    exception_fields: Optional[Dict[str, str]] = None

    @classmethod
    def from_dict(cls, data: dict) -> "APIError":
        if data.get("exception_fields"):
            data["exception_fields"] = data["exception_fields"]
        remapped_data = remap_fields(cls, data)
        return cls(**remapped_data)
