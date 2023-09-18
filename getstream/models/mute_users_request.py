from dataclasses import dataclass, field
from dataclasses_json import config, dataclass_json

from typing import List, Optional


@dataclass_json
@dataclass
class MuteUsersRequest:
    audio: Optional[bool] = field(metadata=config(field_name="audio"), default=None)
    mute_all_users: Optional[bool] = field(
        metadata=config(field_name="mute_all_users"), default=None
    )
    screenshare: Optional[bool] = field(
        metadata=config(field_name="screenshare"), default=None
    )
    user_ids: Optional[List[str]] = field(
        metadata=config(field_name="user_ids"), default=None
    )
    video: Optional[bool] = field(metadata=config(field_name="video"), default=None)
