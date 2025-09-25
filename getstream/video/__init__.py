from typing import Optional, Dict

from getstream.models import CallResponse


class BaseCall:
    def __init__(
        self, client, call_type: str, call_id: str = None, custom_data: Dict = None
    ):
        self.id = call_id
        self.call_type = call_type
        self.client = client
        self.custom_data = custom_data or {}
        self._data: Optional[CallResponse] = None

    def _sync_from_response(self, data):
        if hasattr(data, "call") and isinstance(data.call, CallResponse):
            self.custom_data = data.call.custom
            self._data = data.call

    def connect_openai(
        self, openai_api_key, agent_user_id, model="gpt-4o-realtime-preview"
    ):
        from .openai import get_openai_realtime_client, ConnectionManagerWrapper

        client = get_openai_realtime_client(openai_api_key, self.client.base_url)
        token = self.client.stream.create_token(agent_user_id)
        connection_manager = client.beta.realtime.connect(
            extra_query={
                "call_type": self.call_type,
                "call_id": self.id,
                "api_key": self.client.api_key,
            },
            model=model,
            extra_headers={
                "Authorization": f"Bearer {openai_api_key}",
                "OpenAI-Beta": "realtime=v1",
                "Stream-Authorization": token,
            },
        )

        # Wrap the connection manager to check for errors in the first message
        return ConnectionManagerWrapper(connection_manager, self.call_type, self.id)

    def create_srt_token(self, user_id: str) -> str:
        if self._data is None:
            raise TypeError(
                "call object is not initialized, make sure to call .get or .get_or_create first"
            )

        token = self.client.stream.create_token(user_id)
        passphrase = token.split(".")[2]

        return self._data.ingress.srt.address.replace(
            "{passphrase}", passphrase
        ).replace("{token}", token)
