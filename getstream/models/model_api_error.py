from dataclasses import dataclass
from typing import List, Optional, Dict


@dataclass
class APIError:
    StatusCode: int
    Code: int
    Details: List[int]
    Duration: str
    ExceptionFields: Optional[Dict[str, str]]
    Message: str
    MoreInfo: str

    @classmethod
    def from_dict(cls, data: dict) -> "APIError":
        return cls(**data)
