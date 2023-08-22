from dataclasses import dataclass


@dataclass
class EdgeResponse:
    continent_code: str
    country_iso_code: str
    green: int
    id: str
    latency_test_url: str
    latitude: float
    longitude: float
    red: int
    subdivision_iso_code: str
    yellow: int
