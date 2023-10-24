import json
from typing import Dict, List, Optional
from getstream.chat.models.delete_user_response import DeleteUserResponse
from getstream.chat.models.sort_param import SortParam
from getstream.chat.models.update_users_response import UpdateUsersResponse
from getstream.chat.models.users_response import UsersResponse
from getstream.models.user_request import UserRequest
from getstream.sync.base import BaseClient
from getstream.utils import to_chat_user_dict


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

    def update_users(self, users: Dict[str, UserRequest]) -> UpdateUsersResponse:
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
            query_params=query_params,
            path_params=path_params,
            json=json,
        )
        # loop through chat_response dict, and apply from_chat_user_dict to value on user items
        old_dict = chat_response.data()
        return UpdateUsersResponse.from_dict(old_dict)

    def query_users(
        self,
        filter_conditions: Optional[Dict[str, object]] = {},
        sort: List[SortParam] = None,
        user_id: Optional[str] = None,
        id_gt: Optional[str] = None,
        id_gte: Optional[str] = None,
        presence: Optional[bool] = None,
        user: Optional[UserRequest] = None,
        offset: Optional[int] = None,
        client_id: Optional[str] = None,
        connection_id: Optional[str] = None,
        id_lt: Optional[str] = None,
        id_lte: Optional[str] = None,
        limit: Optional[int] = None,
        **kwargs
    ) -> UsersResponse:
        query_params = {}
        payload = {}
        path_params = {}
        payload["filter_conditions"] = filter_conditions
        payload["sort"] = sort
        payload["user_id"] = user_id
        payload["id_gt"] = id_gt
        payload["id_gte"] = id_gte
        payload["presence"] = presence
        if user is not None:
            payload["user"] = to_chat_user_dict(user)
        payload["offset"] = offset
        payload["client_id"] = client_id
        payload["connection_id"] = connection_id
        payload["id_lt"] = id_lt
        payload["id_lte"] = id_lte
        payload["limit"] = limit
        query_params = {"payload": json.dumps(payload)}

        chat_response = self.get(
            "/users",
            query_params=query_params,
            path_params=path_params,
        )
        old_dict = chat_response.data()

        return UsersResponse.from_dict(old_dict)

    def delete_user(
        self,
        user_id: str,
        user_ids: List[str] = None,
        conversations: Optional[str] = None,
        messages: Optional[str] = None,
        new_channel_owner_id: Optional[str] = None,
        user: Optional[UserRequest] = None,
    ) -> DeleteUserResponse:
        query_params = {}
        path_params = {}
        path_params["user_id"] = user_id
        query_params["user_ids"] = user_ids
        query_params["conversations"] = conversations
        query_params["messages"] = messages
        query_params["new_channel_owner_id"] = new_channel_owner_id
        if user is not None:
            query_params["user"] = to_chat_user_dict(user)

        chat_response = self.delete(
            "/users/{user_id}", query_params=query_params, path_params=path_params
        )
        old_dict = chat_response.data()
        return DeleteUserResponse.from_dict(old_dict)
