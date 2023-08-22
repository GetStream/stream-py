from dataclasses import dataclass
from datetime import datetime


@dataclass
class CallRecording:
    end_time: datetime
    filename: str
    start_time: datetime
    url: str
