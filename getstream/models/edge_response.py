from dataclasses import dataclass, field
from dataclasses_json import config, dataclass_json


@dataclass_json
@dataclass
class EdgeResponse:
    green: int = field(metadata=config(field_name="green"))
    id: str = field(metadata=config(field_name="id"))
    latency_test_url: str = field(metadata=config(field_name="latency_test_url"))
    latitude: float = field(metadata=config(field_name="latitude"))
    red: int = field(metadata=config(field_name="red"))
    yellow: int = field(metadata=config(field_name="yellow"))
    continent_code: str = field(metadata=config(field_name="continent_code"))
    country_iso_code: str = field(metadata=config(field_name="country_iso_code"))
    longitude: float = field(metadata=config(field_name="longitude"))
    subdivision_iso_code: str = field(
        metadata=config(field_name="subdivision_iso_code")
    )
