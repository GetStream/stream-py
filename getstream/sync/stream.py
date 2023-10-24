from getstream import BaseStream
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
        self._token = token or self.create_token()
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
    def users(self):
        return UsersClient(
            api_key=self._api_key,
            base_url=self._chat_base_url,
            token=self._token,
            timeout=self._timeout,
            user_agent=self._user_agent,
        )
        # self.chat = ChatClient(
        #     api_key=api_key, base_url="https://chat.stream-io-api.com", token=token
        # )
