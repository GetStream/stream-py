from dataclasses import dataclass


@dataclass
class UnblockUserRequest:
    user_id: str
