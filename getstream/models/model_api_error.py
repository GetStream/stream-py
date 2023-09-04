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
    exception_fields: Optional[Dict[str, str]]
    message: str
    more_info: str

    @classmethod
    def from_dict(cls, data: dict) -> "APIError":
        remapped_data = remap_fields(cls, data)
        return cls(**remapped_data)
