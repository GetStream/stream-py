from typing import List


class GeofenceSettingsRequest:
    def __init__(self, names: List[str] = None):
        self.names = names if names is not None else []
