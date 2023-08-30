from dataclasses import dataclass


@dataclass
class Response:
    duration: str

    @classmethod
    def from_dict(cls, data: dict) -> "Response":
        return cls(**data)
