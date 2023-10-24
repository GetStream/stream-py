from typing import Dict
from getstream.models.user_request import UserRequest
from getstream.models.user_response import UserResponse

RESERVED_KEYWORDS = [
    "ban_expires",
    "banned",
    "id",
    "invisible",
    "language",
    "push_notifications",
    "revoke_tokens_issued_before",
    "role",
    "teams",
    "created_at",
    "deactivated_at",
    "deleted_at",
    "last_active",
    "online",
    "updated_at",
    "shadow_banned",
    "name",
    "image",
]


def to_chat_user_dict(user: UserRequest) -> Dict[str, object]:
    """
    Convert UserRequest instance to a chat dictionary
    i.e. put chat_dict["custom"] fields to the root level
    """
    # Convert UserRequest instance to dictionary
    chat_dict = user.to_dict()

    # Unpack the custom fields to the root level
    if "custom" in chat_dict and chat_dict["custom"] is not None:
        chat_dict.update(chat_dict["custom"])
        del chat_dict["custom"]

    return chat_dict


def from_chat_user_dict(chat_user: Dict[str, object]) -> UserResponse:
    """
    Reverse operation of to_chat_user_dict
     i.e. put root fields that are not reserved keywords to the "custom" field
    """
    custom_fields = {}
    keys_to_remove = []

    for key, value in chat_user.items():
        # If the key is a reserved keyword, skip it
        if key not in RESERVED_KEYWORDS:
            custom_fields[key] = value
            keys_to_remove.append(key)

    # If there are custom fields, update the dictionary
    if custom_fields:
        chat_user["custom"] = custom_fields
        for key in keys_to_remove:
            del chat_user[key]

    return UserResponse.from_dict(chat_user)
