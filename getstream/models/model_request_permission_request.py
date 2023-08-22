from typing import List


class RequestPermissionRequest:
    def __init__(self, permissions: List[str]):
        self.permissions = permissions
