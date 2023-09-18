from dataclasses import dataclass, field
from dataclasses_json import config, dataclass_json

from datetime import datetime


@dataclass_json
@dataclass
class CallBroadcastingStartedEvent:
    hls_playlist_url: str = field(metadata=config(field_name="hls_playlist_url"))
    type: str = field(metadata=config(field_name="type"))
    call_cid: str = field(metadata=config(field_name="call_cid"))
    created_at: datetime = field(metadata=config(field_name="created_at"))
