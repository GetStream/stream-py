from dataclasses import dataclass
from typing import Optional


@dataclass
class EgressHLSResponse:
    playlist_url: Optional[str] = None

    @classmethod
    def from_dict(cls, data: dict) -> "EgressHLSResponse":
        return cls(**data)
