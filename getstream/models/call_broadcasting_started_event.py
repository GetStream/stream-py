from dataclasses import dataclass, field
from dataclasses_json import config, dataclass_json

from datetime import datetime
from marshmallow import fields


@dataclass_json
@dataclass
class CallBroadcastingStartedEvent:
    call_cid: str = field(metadata=config(field_name="call_cid"))
    created_at: datetime = field(
        metadata=config(
            field_name="created_at",
            encoder=datetime.isoformat,
            decoder=datetime.fromisoformat,
            mm_field=fields.DateTime(format="iso"),
        )
    )
    hls_playlist_url: str = field(metadata=config(field_name="hls_playlist_url"))
    type: str = field(metadata=config(field_name="type"))
