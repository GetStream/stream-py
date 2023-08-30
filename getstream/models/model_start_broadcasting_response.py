from dataclasses import dataclass


@dataclass
class StartBroadcastingResponse:
    duration: str
    playlist_url: str

    @classmethod
    def from_dict(cls, data: dict) -> "StartBroadcastingResponse":
        return cls(**data)
