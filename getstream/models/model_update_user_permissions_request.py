from typing import List, Optional
from dataclasses import dataclass


@dataclass
class UpdateUserPermissionsRequest:
    user_id: str
    grant_permissions: Optional[List[str]] = None
    revoke_permissions: Optional[List[str]] = None

    @classmethod
    def from_dict(cls, data: dict) -> "UpdateUserPermissionsRequest":
        return cls(**data)
