from dataclasses import dataclass


@dataclass
class APNS:
    body: str
    title: str
