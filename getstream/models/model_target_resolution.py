from dataclasses import dataclass


@dataclass
class TargetResolution:
    bitrate: int
    height: int
    width: int
