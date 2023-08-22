from dataclasses import dataclass
from datetime import datetime


@dataclass
class CallBroadcastingStartedEvent:
    call_cid: str
    created_at: datetime
    hls_playlist_url: str
    type: str
