import json
from typing import Dict, List, Optional
from getstream.chat.models.deactivate_user_response import DeactivateUserResponse
from getstream.chat.models.delete_user_response import DeleteUserResponse
from getstream.chat.models.delete_users_response import DeleteUsersResponse
from getstream.chat.models.reactivate_users_response import ReactivateUsersResponse
from getstream.chat.models.sort_param import SortParam
from getstream.chat.models.update_user_partial_request import UpdateUserPartialRequest
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

    def upsert_users(self, users: Dict[str, UserRequest]) -> UpdateUsersResponse:
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
        for key, value in kwargs.items():
            payload[key] = value
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
        mark_messages_deleted: Optional[bool] = None,
        hard_delete: Optional[bool] = None,
        delete_conversation_channels: Optional[bool] = None,
        **kwargs
    ) -> DeleteUserResponse:
        query_params = {}
        path_params = {}
        path_params["user_id"] = user_id
        query_params["mark_messages_deleted"] = mark_messages_deleted
        query_params["hard_delete"] = hard_delete
        query_params["delete_conversation_channels"] = delete_conversation_channels
        for key, value in kwargs.items():
            query_params[key] = value

        chat_response = self.delete(
            "/users/{user_id}", query_params=query_params, path_params=path_params
        )
        old_dict = chat_response.data()
        return DeleteUserResponse.from_dict(old_dict)

    def delete_users(
        self,
        user_ids: List[str] = None,
        conversations: Optional[str] = None,
        messages: Optional[str] = None,
        new_channel_owner_id: Optional[str] = None,
        user: Optional[str] = None,
        **kwargs
    ) -> DeleteUsersResponse:
        query_params = {}
        path_params = {}
        json = {}

        json["user_ids"] = user_ids
        json["conversations"] = conversations
        json["messages"] = messages
        json["new_channel_owner_id"] = new_channel_owner_id
        json["user"] = user
        for key, value in kwargs.items():
            json[key] = value

        chat_response = self.post(
            "/users/delete",
            query_params=query_params,
            path_params=path_params,
            json=json,
        )
        old_dict = chat_response.data()
        return DeleteUsersResponse.from_dict(old_dict)

    def update_users_partial(
        self, users: List[UpdateUserPartialRequest] = None, **kwargs
    ) -> UpdateUsersResponse:
        query_params = {}
        path_params = {}
        json = {}

        json["users"] = [user.to_dict() for user in users]
        for key, value in kwargs.items():
            json[key] = value

        chat_response = self.patch(
            "/users",
            query_params=query_params,
            path_params=path_params,
            json=json,
        )
        old_dict = chat_response.data()
        return UpdateUsersResponse.from_dict(old_dict)

    def deactivate_user(
        self,
        created_by_id: Optional[str] = None,
        mark_messages_deleted: Optional[bool] = None,
        user_id: Optional[str] = None,
        **kwargs
    ) -> DeactivateUserResponse:
        query_params = {}
        path_params = {}
        json = {}
        path_params["user_id"] = user_id
        json["created_by_id"] = created_by_id
        json["mark_messages_deleted"] = mark_messages_deleted
        json["user_id"] = user_id
        for key, value in kwargs.items():
            json[key] = value

        chat_response = self.post(
            "/users/{user_id}/deactivate",
            query_params=query_params,
            path_params=path_params,
            json=json,
        )
        old_dict = chat_response.data()
        return DeactivateUserResponse.from_dict(old_dict)

    def reactivate_users(
        self,
        created_by_id: Optional[str] = None,
        restore_messages: Optional[bool] = None,
        user_ids: List[str] = None,
        **kwargs
    ) -> ReactivateUsersResponse:
        query_params = {}
        path_params = {}
        json = {}
        json["created_by_id"] = created_by_id
        json["restore_messages"] = restore_messages
        json["user_ids"] = user_ids
        for key, value in kwargs.items():
            json[key] = value

        chat_response = self.post(
            "/users/reactivate",
            query_params=query_params,
            path_params=path_params,
            json=json,
        )

        old_dict = chat_response.data()
        return ReactivateUsersResponse.from_dict(old_dict)
