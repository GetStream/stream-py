from typing import Dict, List
from getstream.chat.models.update_users_response import UpdateUsersResponse
from getstream.models.user_request import UserRequest
from getstream.models.user_response import UserResponse
from getstream.sync.base import BaseClient
from getstream.utils import from_chat_user_dict, to_chat_user_dict


class UsersClient(
    BaseClient
):  # TODO: inherit from generated once we fix spec for generation

    def __init__(self, api_key: str, base_url, token, timeout, user_agent):
        super().__init__(
            api_key=api_key,
            base_url=base_url,
            token=token,
            timeout=timeout,
            user_agent=user_agent,
        )

    def update_users(self, users: Dict[str, UserRequest]) -> Dict[str, UserResponse]:
        """
        Update or create users in bulk
        """
        for key, value in users.items():
            users[key] = to_chat_user_dict(value)
        query_params = {}
        path_params = {}
        json = {"users": users}

        chat_response = self.post(
            "/users",
            UpdateUsersResponse,
            query_params=query_params,
            path_params=path_params,
            json=json,
        )
        # loop through chat_response dict, and apply from_chat_user_dict to value on user items
        old_dict = chat_response.data().to_dict()

        for key, value in old_dict["users"].items():
            old_dict[key] = from_chat_user_dict(value)
        return old_dict
