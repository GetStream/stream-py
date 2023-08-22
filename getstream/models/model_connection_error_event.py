from dataclasses import dataclass
from datetime import datetime
from typing import Optional


@dataclass
class ConnectionErrorEvent:
    connection_id: str
    created_at: datetime
    error: NullableAPIError
    type: str
