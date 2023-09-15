from dataclasses import dataclass, field

from dataclasses_json import config, dataclass_json


@dataclass_json
@dataclass
class StartBroadcastingResponse:
    duration: str = field(metadata=config(field_name="duration"))
    playlist_url: str = field(metadata=config(field_name="playlist_url"))
