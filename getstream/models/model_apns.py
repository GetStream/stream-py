from dataclasses import dataclass


@dataclass
class APNS:
    body: str
    title: str

    @classmethod
    def from_dict(cls, data: dict) -> "APNS":
        return cls(**data)
