from dataclasses import dataclass


@dataclass
class RTMPIngress:
    address: str

    @classmethod
    def from_dict(cls, data: dict) -> "RTMPIngress":
        return cls(**data)
