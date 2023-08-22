from dataclasses import dataclass
from datetime import datetime


@dataclass
class HealthCheckEvent:
    connection_id: str
    created_at: datetime
    type: str
