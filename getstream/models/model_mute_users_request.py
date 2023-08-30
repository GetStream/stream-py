from typing import List, Optional
from dataclasses import dataclass


@dataclass
class MuteUsersRequest:
    audio: Optional[bool] = None
    mute_all_users: Optional[bool] = None
    screenshare: Optional[bool] = None
    user_ids: List[str] = None
    video: Optional[bool] = None

    @classmethod
    def from_dict(cls, data: dict) -> "MuteUsersRequest":
        return cls(**data)
