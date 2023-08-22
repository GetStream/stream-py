from typing import List, Optional
from dataclasses import dataclass


@dataclass
class UpdateUserPermissionsRequest:
    grant_permissions: Optional[List[str]] = None
    revoke_permissions: Optional[List[str]] = None
    user_id: str
