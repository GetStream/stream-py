from dataclasses import dataclass


@dataclass
class StartBroadcastingResponse:
    duration: str
    playlist_url: str
