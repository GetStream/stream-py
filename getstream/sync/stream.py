from typing import Dict, List, Optional
from getstream import BaseStream
from getstream.chat.models.delete_user_response import DeleteUserResponse
from getstream.chat.models.sort_param import SortParam
from getstream.chat.models.update_users_response import UpdateUsersResponse
from getstream.chat.models.users_response import UsersResponse
from getstream.models.user_request import UserRequest
from getstream.users.sync.client import UsersClient

# from getstream.chat.sync import ChatClient

from functools import cached_property

from getstream.video.sync.client import VideoClient


class Stream(BaseStream):
    """
    A class used to represent a Stream client.

    Contains methods to interact with Video and Chat modules of Stream API.
    """

    BASE_URL = "stream-io-api.com"

    def __init__(
        self,
        api_key: str,
        api_secret: str,
        token=None,
        timeout=None,
        user_agent=None,
        video_base_url=None,
        chat_base_url=None,
    ):
        """
        Instantiates the Stream client with provided credentials, and initializes the chat and video clients.

        If a token is not provided, it will be automatically generated.
        If a base URL for the video client is not provided, it will use the default value 'https://video.stream-io-api.com/video'.

        Parameters:
        - api_key (str): The API key for your Stream app.
        - api_secret (str): The API secret for your Stream app.
        - token (str, optional): The token used to authenticate against the Stream API. Defaults to None.
        - timeout (int, optional): Time in seconds to wait for a response from the API before timing out. Defaults to None.
        - user_agent (str, optional): String representing the user-agent to pass when making requests to the Stream API. Defaults to None.
        - video_base_url (str, optional): Base API URL for making video related requests. Defaults to None.
        """

        super().__init__(api_key, api_secret)

        self._api_key = api_key
        self._token = token or self._create_token()
        self._timeout = timeout
        self._user_agent = user_agent
        self._video_base_url = video_base_url or f"https://video.{self.BASE_URL}/video"
        self._chat_base_url = chat_base_url or f"https://chat.{self.BASE_URL}"

    @cached_property
    def video(self):
        return VideoClient(
            api_key=self._api_key,
            base_url=self._video_base_url,
            token=self._token,
            timeout=self._timeout,
            user_agent=self._user_agent,
        )

    @cached_property
    def _users(self):
        return UsersClient(
            api_key=self._api_key,
            base_url=self._chat_base_url,
            token=self._token,
            timeout=self._timeout,
            user_agent=self._user_agent,
        )

    def upsert_users(self, users: Dict[str, UserRequest]) -> UpdateUsersResponse:
        return self._users.upsert_users(users=users)

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
        return self._users.query_users(
            filter_conditions=filter_conditions,
            sort=sort,
            user_id=user_id,
            id_gt=id_gt,
            id_gte=id_gte,
            presence=presence,
            user=user,
            offset=offset,
            client_id=client_id,
            connection_id=connection_id,
            id_lt=id_lt,
            id_lte=id_lte,
            limit=limit,
            **kwargs
        )

    def delete_user(
        self,
            user_id: str,
            mark_messages_deleted: Optional[bool] = None,
            hard_delete: Optional[bool] = None,
            delete_conversation_channels: Optional[bool] = None,
            **kwargs

    ) -> DeleteUserResponse:
        return self._users.delete_user(
            user_id=user_id,
            mark_messages_deleted=mark_messages_deleted,
            hard_delete=hard_delete,
            delete_conversation_channels=delete_conversation_channels,
            **kwargs

        )

    def delete_users(
        self,
        user_ids: List[str] = None,
        conversations: Optional[str] = None,
        messages: Optional[str] = None,
        new_channel_owner_id: Optional[str] = None,
        user: Optional[str] = None,
        **kwargs
    ) -> DeleteUserResponse:
        """
        user_ids: the list of user ids to delete
        new_channel_owner_id: the new owner of the channels of the deleted user
        user: user delete mode
            soft: marks user as deleted and retains all user data
            pruning: marks user as deleted and nullifies user information
            hard: deletes user completely. Requires 'hard' option for messages and conversations as well
        conversations: conversation channels delete mode
            null or empty string: doesn't delete any conversation channels
            soft: marks all user messages as deleted without removing any related message data
            pruning: marks all user messages as deleted, nullifies message information and removes some message data such as reactions and flags
            hard: deletes messages completely with all related information
        """
        return self._users.delete_users(
            user_ids=user_ids,
            conversations=conversations,
            messages=messages,
            new_channel_owner_id=new_channel_owner_id,
            user=user,
            **kwargs

        )
     # self.chat = ChatClient(
        #     api_key=api_key, base_url="https://chat.stream-io-api.com", token=token
        # )
