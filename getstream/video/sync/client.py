from getstream.sync.base import BaseClient
from getstream.video.exceptions import VideoCallTypeBadRequest


class VideoClient(BaseClient):
    def __init__(self, api_key: str, base_url, token, timeout, user_agent):
        super().__init__(
            api_key=api_key,
            base_url=base_url,
            token=token,
            timeout=timeout,
            user_agent=user_agent,
        )

    def call(self, call_type: str, callid: str):
        return Call(self, call_type, callid)

    def edges(self):
        response = self.get("/edges")
        json = response.json()
        return json

    def get_edge_server(self, call_type: str, callid: str, data):
        response = self.get(f"/calls/{call_type}/{callid}/get_edge_server", json=data)
        json = response.json()
        return json

    def create_call_type(self, data):
        response = self.post("/calltypes", json=data)
        if response.status_code == 400:
            error_json = response.json()
            message = error_json.pop("message", None)
            code = error_json.pop("code", None)
            status_code = error_json.pop("StatusCode", None)
            raise VideoCallTypeBadRequest(
                message=message, code=code, status_code=status_code
            )
        return response.json()

    def get_call_type(self, name: str):
        response = self.get(f"/calltypes/{name}")
        if response.status_code == 400:
            error_json = response.json()
            message = error_json.pop("message", None)
            code = error_json.pop("code", None)
            status_code = error_json.pop("StatusCode", None)
            raise VideoCallTypeBadRequest(
                message=message, code=code, status_code=status_code
            )
        return response.json()

    def list_call_types(self):
        response = self.get("/calltypes")
        if response.status_code == 400:
            error_json = response.json()
            message = error_json.pop("message", None)
            code = error_json.pop("code", None)
            status_code = error_json.pop("StatusCode", None)
            raise VideoCallTypeBadRequest(
                message=message, code=code, status_code=status_code
            )
        json = response.json()
        return json

    def update_call_type(self, name: str, data):
        response = self.put(f"/calltypes/{name}", json=data)
        if response.status_code == 400:
            error_json = response.json()
            message = error_json.pop("message", None)
            code = error_json.pop("code", None)
            status_code = error_json.pop("StatusCode", None)
            raise VideoCallTypeBadRequest(
                message=message, code=code, status_code=status_code
            )
        return response.json()

    def query_calls(self, data):
        response = self.post("/calls", json=data)
        return response.json()

    def block_user(self, call_type: str, callid: str, data):
        response = self.post(f"/call/{call_type}/{callid}/block", json=data)
        return response.json()

    def end_call(self, call_type: str, callid: str):
        response = self.post(f"/call/{call_type}/{callid}/mark_ended")
        return response.json()

    def get_call(self, call_type: str, callid: str):
        response = self.get(f"/call/{call_type}/{callid}")
        return response.json()

    def go_live(self, call_type: str, callid: str):
        response = self.post(f"/call/{call_type}/{callid}/go_live")
        return response.json()

    def join_call(self, call_type: str, callid: str, data):
        response = self.post(f"/call/{call_type}/{callid}/join", data=data)
        return response.json()

    def delete_call_type(self, name: str):
        response = self.delete(f"/calltypes/{name}")
        if response.status_code == 400:
            error_json = response.json()
            message = error_json.pop("message", None)
            code = error_json.pop("code", None)
            status_code = error_json.pop("StatusCode", None)
            raise VideoCallTypeBadRequest(
                message=message, code=code, status_code=status_code
            )
        return response.json()

    def delete_recording(
        self, call_type: str, callid: str, sessionid: str, recordingid: str
    ):
        response = self.delete(
            f"/call/{call_type}/{callid}/{sessionid}/recordings/{recordingid}"
        )
        return response.json()

    def add_device(
        self, id, push_provider, push_provider_name=None, user_id=None, voip_token=None
    ):
        data = {"id": id, "push_provider": push_provider, "voip_token": voip_token}
        if user_id is not None:
            data.update({"user_id": user_id})
        if push_provider_name is not None:
            data.update({"push_provider_name": push_provider_name})
        response = self.post("/devices", json=data)
        return response.json()

    def add_voip_device(self, id, push_provider, push_provider_name=None, user_id=None):
        self.add_device(id, push_provider, push_provider_name, user_id, voip_token=True)

    def get_devices(self):
        response = self.get("/devices")
        return response.json()

    def remove_device(self, data):
        response = self.delete("/devices", json=data)
        return response.json()

    def query_recordings(self, call_type: str, callid: str, sessionid: str):
        response = self.get(f"/call/{call_type}/{callid}/{sessionid}/recordings")
        return response.json()

    def mute_users(self, call_type: str, callid: str, data):
        response = self.post(f"/call/{call_type}/{callid}/mute_users", data=data)
        return response.json()

    def query_members(self, call_type: str, callid: str, data):
        response = self.post(f"/call/{call_type}/{callid}/members", json=data)
        return response.json()

    def request_permissions(self, call_type: str, callid: str, data):
        response = self.post(
            f"/call/{call_type}/{callid}/request_permission", json=data
        )
        return response.json()

    def send_custom_event(self, call_type: str, callid: str, data):
        response = self.post(f"/call/{call_type}/{callid}/event", json=data)
        return response.json()

    def send_reaction(self, call_type: str, callid: str, data):
        response = self.post(f"/call/{call_type}/{callid}/reaction", json=data)
        return response.json()

    def start_recording(self, call_type: str, callid: str):
        response = self.post(f"/call/{call_type}/{callid}/start_recording")
        return response.json()

    def start_trancription(self, call_type: str, callid: str):
        response = self.post(f"/call/{call_type}/{callid}/start_transcription")
        return response.json()

    def start_broadcasting(self, call_type: str, callid: str):
        response = self.post(f"/call/{call_type}/{callid}/start_broadcasting")
        return response.json()

    def stop_recording(self, call_type: str, callid: str):
        response = self.post(f"/call/{call_type}/{callid}/stop_recording")
        return response.json()

    def stop_transcription(self, call_type: str, callid: str):
        response = self.post(f"/call/{call_type}/{callid}/stop_transcription")
        return response.json()

    def stop_broadcasting(self, call_type: str, callid: str):
        response = self.post(f"/call/{call_type}/{callid}/stop_broadcasting")
        return response.json()

    def stop_live(self, call_type: str, callid: str):
        response = self.post(f"/call/{call_type}/{callid}/stop_live")
        return response.json()

    def unblock_user(self, call_type: str, callid: str, data):
        response = self.post(f"/call/{call_type}/{callid}/unblock", json=data)
        return response.json()

    def update_call_members(self, call_type: str, callid: str, members: list = None):
        data = {"update_members": members}
        response = self.put(f"/call/{call_type}/{callid}/members", json=data)
        return response.json()

    def update_call(self, call_type: str, callid: str, data):
        request_data = {"data": data}
        response = self.put(f"/call/{call_type}/{callid}", json=request_data)
        return response.json()

    def update_user_permissions(self, call_type: str, callid: str, data):
        response = self.put(f"/call/{call_type}/{callid}/permissions", json=data)
        return response.json()

    def get_or_create_call(
        self, call_type: str, callid: str, data: dict, members: list = None
    ):
        request_data = {"data": data}
        if members is not None:
            request_data.update({"members": members})
        response = self.post(f"/call/{call_type}/{callid}", json=request_data)
        return response.json()


class Call:
    def __init__(self, client: VideoClient, call_type: str, callid: str):
        self._client = client
        self._call_type = call_type
        self._callid = callid

    def create(self, data: dict, members: list = None):
        return self._client.get_or_create_call(
            self._call_type, self._callid, data, members
        )

    def get(self):
        return self._client.get_call(self._call_type, self._callid)

    def update(self, data: dict):
        return self._client.update_call(self._call_type, self._callid, data)

    def update_user_permissions(self, data):
        return self._client.update_user_permissions(self._call_type, self._callid, data)

    def update_call_members(self, data, members: list = None):
        return self._client.update_call_members(
            self._call_type, self._callid, data, members
        )

    def unblock_user(self, data):
        return self._client.unblock_user(self._call_type, self._callid, data)

    def stop_live(self):
        return self._client.stop_live(self._call_type, self._callid)

    def query_recordings(self, sessionid: str):
        return self._client.query_recordings(self._call_type, self._callid, sessionid)

    def delete_recording(self, sessionid: str, recordingid: str):
        return self._client.delete_recording(
            self._call_type, self._callid, sessionid, recordingid
        )

    def mute_users(self, data):
        return self._client.mute_users(self._call_type, self._callid, data)

    def query_members(self, data):
        return self._client.query_members(self._call_type, self._callid, data)

    def request_permissions(self, data):
        return self._client.request_permissions(self._call_type, self._callid, data)

    def send_custom_event(self, data):
        return self._client.send_custom_event(self._call_type, self._callid, data)

    def send_reaction(self, data):
        return self._client.send_reaction(self._call_type, self._callid, data)

    def start_recording(self):
        return self._client.start_recording(self._call_type, self._callid)

    def start_trancription(self):
        return self._client.start_trancription(self._call_type, self._callid)

    def start_broadcasting(self):
        return self._client.start_broadcasting(self._call_type, self._callid)

    def stop_recording(self):
        return self._client.stop_recording(self._call_type, self._callid)

    def stop_transcription(self):
        return self._client.stop_transcription(self._call_type, self._callid)

    def stop_broadcasting(self):
        return self._client.stop_broadcasting(self._call_type, self._callid)

    def block_user(self, data):
        return self._client.block_user(self._call_type, self._callid, data)

    def end_call(self):
        return self._client.end_call(self._call_type, self._callid)

    def go_live(self):
        return self._client.go_live(self._call_type, self._callid)

    def join(self, data):
        return self._client.join_call(self._call_type, self._callid, data)
