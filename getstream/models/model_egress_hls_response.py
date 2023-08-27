from dataclasses import dataclass


@dataclass
class EgressHLSResponse:
    playlist_url: str

    @classmethod
    def from_dict(cls, data: dict) -> "EgressHLSResponse":
        return cls(**data)
