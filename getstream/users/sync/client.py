# from datetime import datetime
from datetime import datetime
import json
from typing import Dict, List, Optional
from getstream.chat.models.ban_response import BanResponse
from getstream.chat.models.delete_user_response import DeleteUserResponse
from getstream.chat.models.delete_users_request import DeleteUsersRequest
from getstream.chat.models.flag_response import FlagResponse
from getstream.chat.models.query_banned_users_response import QueryBannedUsersResponse
from getstream.chat.models.sort_param import SortParam
from getstream.chat.models.update_users_response import UpdateUsersResponse
from getstream.chat.models.users_response import UsersResponse
# from getstream.chat.models.flag_response import FlagResponse
# from getstream.chat.models.mute_user_response import MuteUserResponse
# from getstream.chat.models.query_banned_users_response import QueryBannedUsersResponse
# from getstream.chat.models.sort_param import SortParam
# from getstream.chat.models.users_response import UsersResponse
from getstream.models.create_guest_response import CreateGuestResponse
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
        # for key, value in old_dict["users"].items():
        #     old_dict[key] = from_chat_user_dict(value)
        return UpdateUsersResponse.from_dict(old_dict)

    # it's already in video sdk so do we really need this
    # def create_guest(self, guest: UserRequest) -> CreateGuestResponse:
    #     """
    #     Create a guest user
    #     """
    #     query_params = {}
    #     path_params = {}
    #     json = {}
    #     json["user"] = to_chat_user_dict(guest)

    #     chat_response = self.post(
    #         "/guest",
    #         query_params=query_params,
    #         path_params=path_params,
    #         json=json,
    #     )
    #     old_dict = chat_response.data()
    #     old_dict["user"] = from_chat_user_dict(old_dict["user"])
    #     return CreateGuestResponse.from_dict(old_dict)

    # def ban_user(self, target_user_id: str, banned_by_id: Optional[str] = None,
    #              id: Optional[str] = None, user: Optional[UserRequest] = None,
    #              banned_by: Optional[UserRequest] = None, ip_ban: Optional[bool] = None,
    #              reason: Optional[str] = None, shadow: Optional[bool] = None,
    #              timeout: Optional[int] = None, type: Optional[str] = None,
    #              user_id: Optional[str] = None, ) -> BanResponse:
    #     query_params = {}
    #     path_params = {}
    #     json = {}
    #     json["target_user_id"] = target_user_id
    #     json["banned_by_id"] = banned_by_id
    #     json["id"] = id
    #     if user is not None:
    #         json["user"] = to_chat_user_dict(user)
    #     if user is not None:
    #         json["banned_by"] = to_chat_user_dict(banned_by)
    #     json["ip_ban"] = ip_ban
    #     json["reason"] = reason
    #     json["shadow"] = shadow
    #     json["timeout"] = timeout
    #     json["type"] = type
    #     json["user_id"] = user_id

    #     chat_response = self.post("/moderation/ban", query_params=query_params,
    #                               path_params=path_params,
    #                               json=json,)
    #     old_dict = chat_response.data()
    #     # old_dict["user"] = from_chat_user_dict(old_dict["user"])
    #     # old_dict["banned_by"] = from_chat_user_dict(old_dict["banned_by"])
    #     return BanResponse.from_dict(old_dict)

    # def unban_user(self, target_user_id: str, banned_by_id: Optional[str] = None,
    #                id: Optional[str] = None, user: Optional[UserRequest] = None,
    #                banned_by: Optional[UserRequest] = None, ip_ban: Optional[bool] = None,
    #                reason: Optional[str] = None, shadow: Optional[bool] = None,
    #                timeout: Optional[int] = None, type: Optional[str] = None,
    #                user_id: Optional[str] = None, ) -> BanResponse:
    #     query_params = {}
    #     path_params = {}
    #     json = {}
    #     query_params["target_user_id"] = target_user_id
    #     query_params["banned_by_id"] = banned_by_id
    #     query_params["id"] = id
    #     if user is not None:
    #         query_params["user"] = to_chat_user_dict(user)
    #     if user is not None:
    #         query_params["banned_by"] = to_chat_user_dict(banned_by)
    #     query_params["ip_ban"] = ip_ban
    #     query_params["reason"] = reason
    #     query_params["shadow"] = shadow
    #     query_params["timeout"] = timeout
    #     query_params["type"] = type
    #     query_params["user_id"] = user_id

    #     chat_response = self.delete("/moderation/ban", query_params=query_params,
    #                                 path_params=path_params,
    #                                 )
    #     old_dict = chat_response.data()
    #     # old_dict["user"] = from_chat_user_dict(old_dict["user"])
    #     # old_dict["banned_by"] = from_chat_user_dict(old_dict["banned_by"])
    #     return BanResponse.from_dict(old_dict)

    # def flag(self, target_message_id: Optional[str] = None, target_user_id: Optional[str] = None,
    #          user: Optional[UserRequest] = None, user_id: Optional[str] = None) -> FlagResponse:
    #     query_params = {}
    #     path_params = {}
    #     json = {}
    #     json["target_message_id"] = target_message_id
    #     json["target_user_id"] = target_user_id
    #     json["user"] = to_chat_user_dict(user)
    #     json["user_id"] = user_id

    #     chat_response = self.post("/moderation/flag", query_params=query_params,
    #                               path_params=path_params,
    #                               json=json,)
    #     old_dict = chat_response.data().to_dict()
    #     old_dict["flag"]["user"] = from_chat_user_dict(old_dict["flag"]["user"])
    #     return FlagResponse.from_dict(old_dict)

    # def unflag(self, target_message_id: Optional[str] = None, target_user_id: Optional[str] = None,
    #            user: Optional[UserRequest] = None, user_id: Optional[str] = None) -> FlagResponse:
    #     query_params = {}
    #     path_params = {}
    #     json = {}
    #     json["target_message_id"] = target_message_id
    #     json["target_user_id"] = target_user_id
    #     json["user"] = to_chat_user_dict(user)
    #     json["user_id"] = user_id

    #     chat_response = self.post("/moderation/flag", query_params=query_params,
    #                               path_params=path_params,
    #                               json=json,)
    #     old_dict = chat_response.data().to_dict()
    #     old_dict["flag"]["user"] = from_chat_user_dict(old_dict["flag"]["user"])
    #     return FlagResponse.from_dict(old_dict)

    # def query_banned_users(self, filter_conditions: Dict[str, object] = None,
    #                        offset: Optional[int] = None, user: Optional[UserRequest] = None,
    #                        user_id: Optional[str] = None,
    #                        created_at_after_or_equal: Optional[datetime] = None,
    #                        created_at_before: Optional[datetime] = None,
    #                        created_at_before_or_equal: Optional[datetime] = None,
    #                        limit: Optional[int] = None, sort: Optional[List[SortParam]] = None,
    #                        created_at_after: Optional[datetime] = None) -> QueryBannedUsersResponse:
    #     query_params = {}
    #     path_params = {}
    #     query_params["filter_conditions"] = filter_conditions
    #     query_params["offset"] = offset
    #     query_params["user"] = to_chat_user_dict(user)
    #     query_params["user_id"] = user_id
    #     query_params["created_at_after_or_equal"] = created_at_after_or_equal
    #     query_params["created_at_before"] = created_at_before
    #     query_params["created_at_before_or_equal"] = created_at_before_or_equal
    #     query_params["limit"] = limit
    #     query_params["sort"] = sort
    #     query_params["created_at_after"] = created_at_after

    #     chat_response = self.get("/query_banned_users", query_params=query_params,
    #                              path_params=path_params,
    #                              )
    #     old_dict = chat_response.data().to_dict()

    #     # for key, value in old_dict["bans"].items():
    #     #     old_dict[key]["banned_by"] = from_chat_user_dict(value["banned_by"])
    #     #     old_dict[key]["user"] = from_chat_user_dict(value["user"])

    #     return QueryBannedUsersResponse.from_dict(old_dict)

    def query_users(self, filter_conditions: Optional[Dict[str, object]] = {},
                    sort: List[SortParam] = None, user_id: Optional[str] = None,
                    id_gt: Optional[str] = None, id_gte: Optional[str] = None,
                    presence: Optional[bool] = None, user: Optional[UserRequest] = None,
                    offset: Optional[int] = None, client_id: Optional[str] = None,
                    connection_id: Optional[str] = None, id_lt: Optional[str] = None,
                    id_lte: Optional[str] = None, limit: Optional[int] = None) -> UsersResponse:

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

        chat_response = self.get("/users", query_params=query_params,
                                 path_params=path_params,
                                 )
        old_dict = chat_response.data()
        # for key, value in old_dict["users"].items():
        #     old_dict[key] = from_chat_user_dict(value)

        return UsersResponse.from_dict(old_dict)

    # user_ids: List[str] = field(metadata=config(field_name="user_ids"))
    # conversations: Optional[str] = field(
    #     metadata=config(field_name="conversations"), default=None
    # )
    # messages: Optional[str] = field(
    #     metadata=config(field_name="messages"), default=None
    # )
    # new_channel_owner_id: Optional[str] = field(
    #     metadata=config(field_name="new_channel_owner_id"), default=None
    # )
    # user: Optional[str] = field(metadata=config(field_name="user"), default=None)

    def delete_user(self,
                    user_id: str,
                    user_ids: List[str] = None,
                    conversations: Optional[str] = None,
                    messages: Optional[str] = None,
                    new_channel_owner_id: Optional[str] = None,
                    user: Optional[UserRequest] = None) -> DeleteUserResponse:
        query_params = {}
        path_params = {}
        path_params["user_id"] = user_id
        query_params["user_ids"] = user_ids
        query_params["conversations"] = conversations
        query_params["messages"] = messages
        query_params["new_channel_owner_id"] = new_channel_owner_id
        if user is not None:
            query_params["user"] = to_chat_user_dict(user)

        chat_response = self.delete("/users/{user_id}", query_params=query_params,
                                    path_params=path_params
                                    )
        old_dict = chat_response.data()
        return DeleteUserResponse.from_dict(old_dict)

    # def mute_user(self,
    #               target_ids: List[str],
    #               timeout: Optional[int] = None,
    #               user: Optional[UserRequest] = None,
    #               user_id: Optional[str] = None,
    #               ) -> MuteUserResponse:
    #     query_params = {}
    #     path_params = {}
    #     json = {}
    #     json["target_ids"] = target_ids
    #     json["timeout"] = timeout
    #     json["user"] = to_chat_user_dict(user)
    #     json["user_id"] = user_id

    #     chat_response = self.post("/moderation/mute", query_params=query_params,
    #                               path_params=path_params,
    #                               json=json,)
    #     old_dict = chat_response.data().to_dict()
    #     old_dict["mute"]["user"] = from_chat_user_dict(old_dict["mute"]["user"])
    #     old_dict["mute"]["target"] = from_chat_user_dict(old_dict["mute"]["target"])
    #     for key, value in old_dict["mutes"].items():
    #         old_dict[key]["user"] = from_chat_user_dict(value["user"])
    #         old_dict[key]["target"] = from_chat_user_dict(value["target"])
    #     for key, value in old_dict["own_user"]["mutes"].items():
    #         old_dict["own_user"]["mutes"][key]["user"] = from_chat_user_dict(value["user"])
    #         old_dict["own_user"]["mutes"][key]["target"] = from_chat_user_dict(value["target"])

    # def unmute_user(self, target_id: str, user: Optional[UserRequest] = None,
    #                 user_id: Optional[str] = None, ) -> MuteUserResponse:
    #     query_params = {}
    #     path_params = {}
    #     json = {}
    #     json["target_id"] = target_id
    #     json["user"] = to_chat_user_dict(user)
    #     json["user_id"] = user_id

    #     chat_response = self.post("/moderation/unmute", query_params=query_params,
    #                               path_params=path_params,
    #                               json=json,)
    #     old_dict = chat_response.data().to_dict()
    #     old_dict["mute"]["user"] = from_chat_user_dict(old_dict["mute"]["user"])
    #     old_dict["mute"]["target"] = from_chat_user_dict(old_dict["mute"]["target"])
    #     for key, value in old_dict["mutes"].items():
    #         old_dict[key]["user"] = from_chat_user_dict(value["user"])
    #         old_dict[key]["target"] = from_chat_user_dict(value["target"])
    #     for key, value in old_dict["own_user"]["mutes"].items():
    #         old_dict["own_user"]["mutes"][key]["user"] = from_chat_user_dict(value["user"])
    #         old_dict["own_user"]["mutes"][key]["target"] = from_chat_user_dict(value["target"])
    #     return MuteUserResponse.from_dict(old_dict)
