from dataclasses import dataclass


@dataclass
class ScreensharingSettings:
    access_request_enabled: bool
    enabled: bool
