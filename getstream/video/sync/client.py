from getstream.sync.base import BaseClient
from getstream.video.exceptions import VideoCallTypeBadRequest, VideoClientError


class VideoClient(BaseClient):
    def __init__(self, api_key: str, base_url, token, timeout, user_agent):
        super().__init__(
            api_key=api_key,
            base_url=base_url,
            token=token,
            timeout=timeout,
            user_agent=user_agent,
        )

    def _ensure_success_response(self, response, method, url):
        if not 200 <= response.status_code < 300:
            error_json = response.json()
            message = error_json.pop("message", None)
            code = error_json.pop("code", None)
            status_code = error_json.pop("StatusCode", None)
            error_message = (
            f'Request Failed.\n'
            f'URL: {url}, METHOD: {method}\n'
            f'STATUS CODE: {status_code}\n'
            f'CODE: {code}\n'
            f'REASON: {message}'
            )
            raise VideoClientError(error_message)
            
    def call(self, call_type: str, call_id: str):
        return Call(self, call_type, call_id)

    def edges(self):
        response = self.get("/edges")
        self._ensure_success_response(response, 'GET', '/edges')
        return response.json()
    
    def get_edge_server(self, call_type: str, call_id: str, data):
        response = self.get(f"/calls/{call_type}/{call_id}/get_edge_server", json=data)
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
        self._ensure_success_response(response, 'POST', '/calls')
        return response.json()

    def block_user(self, call_type: str, call_id: str, data):
        path = f"/call/{call_type}/{call_id}/block"
        response = self.post(path, json=data)
        self._ensure_success_response(response, 'POST', path)
        return response.json()

    def end_call(self, call_type: str, call_id: str):
        path = f"/call/{call_type}/{call_id}/mark_ended"
        response = self.post(path)
        self._ensure_success_response(response, 'POST', path)
        return response.json()

    def get_call(self, call_type: str, call_id: str):
        path = f"/call/{call_type}/{call_id}"
        response = self.get(path)
        self._ensure_success_response(response, 'GET', path)
        return response.json()

    def go_live(self, call_type: str, call_id: str):
        path = f"/call/{call_type}/{call_id}/go_live"
        response = self.post(path)
        self._ensure_success_response(response, 'POST', path)
        return response.json()

    def join_call(self, call_type: str, call_id: str, data):
        path = f"/call/{call_type}/{call_id}/join"
        response = self.post(path, data=data)
        self._ensure_success_response(response, 'POST', path)
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
        self, call_type: str, call_id: str, session_id: str, recordingid: str
    ):
        path = f"/call/{call_type}/{call_id}/{session_id}/recordings/{recordingid}"
        response = self.delete(
           path
        )
        self._ensure_success_response(response, 'DELETE', path)
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
        self._ensure_success_response(response, 'POST', '/devices')
        return response.json()

    def add_voip_device(self, id, push_provider, push_provider_name=None, user_id=None):
        self.add_device(id, push_provider, push_provider_name, user_id, voip_token=True)

    def get_devices(self):
        response = self.get("/devices")
        self._ensure_success_response(response, 'GET', '/devices')
        return response.json()

    def remove_device(self, data):
        response = self.delete("/devices", json=data)
        self._ensure_success_response(response, 'DELETE', '/devices')
        return response.json()

    def query_recordings(self, call_type: str, call_id: str, session_id: str = None):
        path = f"/call/{call_type}/{call_id}/recordings"
        if session_id is None:
            path = f"/call/{call_type}/{call_id}/{session_id}/recordings"
            response = self.get(path)
        self._ensure_success_response(response, 'GET', path)
        return response.json()

    def mute_users(self, call_type: str, call_id: str, data):
        path = f"/call/{call_type}/{call_id}/mute_users"
        response = self.post(path, data=data)
        self._ensure_success_response(response, 'POST', path)
        return response.json()

    def query_members(self, call_type: str, call_id: str, data):
        path = f"/call/{call_type}/{call_id}/members"
        response = self.post(path, json=data)
        self._ensure_success_response(response, 'POST', path)
        return response.json()

    def request_permissions(self, call_type: str, call_id: str, data):
        path = f"/call/{call_type}/{call_id}/request_permission"
        response = self.post(
            path, json=data
        )
        self._ensure_success_response(response, 'POST', path)
        return response.json()

    def send_custom_event(self, call_type: str, call_id: str, data):
        path = f"/call/{call_type}/{call_id}/event"
        response = self.post(path, json=data)
        self._ensure_success_response(response, 'POST', path)
        return response.json()

    def send_reaction(self, call_type: str, call_id: str, data):
        path = f"/call/{call_type}/{call_id}/reaction"
        response = self.post(path, json=data)
        self._ensure_success_response(response, 'POST', path)
        return response.json()

    def start_recording(self, call_type: str, call_id: str):
        path = f"/call/{call_type}/{call_id}/start_recording"
        response = self.post(path)
        self._ensure_success_response(response, 'POST', path)
        return response.json()

    def start_trancription(self, call_type: str, call_id: str):
        path = f"/call/{call_type}/{call_id}/start_transcription"
        response = self.post(path)
        self._ensure_success_response(response, 'POST', path)
        return response.json()

    def start_broadcasting(self, call_type: str, call_id: str):
        path = f"/call/{call_type}/{call_id}/start_broadcasting"
        response = self.post(path)
        self._ensure_success_response(response, 'POST', path)
        return response.json()

    def stop_recording(self, call_type: str, call_id: str):
        path = f"/call/{call_type}/{call_id}/stop_recording"
        response = self.post(path)
        self._ensure_success_response(response, 'POST', path)
        return response.json()

    def stop_transcription(self, call_type: str, call_id: str):
        path = f"/call/{call_type}/{call_id}/stop_transcription"
        response = self.post(path)
        self._ensure_success_response(response, 'POST', path)
        return response.json()

    def stop_broadcasting(self, call_type: str, call_id: str):
        path = f"/call/{call_type}/{call_id}/stop_broadcasting"
        response = self.post(path)
        self._ensure_success_response(response, 'POST', path)
        return response.json()

    def stop_live(self, call_type: str, call_id: str):
        path = f"/call/{call_type}/{call_id}/stop_live"
        response = self.post(path)
        self._ensure_success_response(response, 'POST', path)
        return response.json()

    def unblock_user(self, call_type: str, call_id: str, data):
        path = f"/call/{call_type}/{call_id}/unblock"
        response = self.post(path, json=data)
        self._ensure_success_response(response, 'POST', path)
        return response.json()

    def update_call_members(self, call_type: str, call_id: str, members: list = None):
        data = {"update_members": members}
        path = f"/call/{call_type}/{call_id}/members"
        response = self.put(path, json=data)
        self._ensure_success_response(response, 'PUT', path)
        return response.json()

    def update_call(self, call_type: str, call_id: str, data):
        request_data = {"data": data}
        path = f"/call/{call_type}/{call_id}"
        response = self.put(path, json=request_data)
        self._ensure_success_response(response, 'PUT', path)
        return response.json()

    def update_user_permissions(self, call_type: str, call_id: str, data):
        path = f"/call/{call_type}/{call_id}/permissions"
        response = self.put(path, json=data)
        self._ensure_success_response(response, 'PUT', path)
        return response.json()

    def get_or_create_call(
        self, call_type: str, call_id: str, data: dict, members: list = None
    ):
        request_data = {"data": data}
        if members is not None:
            request_data.update({"members": members})
        response = self.post(f"/call/{call_type}/{call_id}", json=request_data)
        return response.json()


class Call:
    def __init__(self, client: VideoClient, call_type: str, call_id: str):
        self._client = client
        self._call_type = call_type
        self._call_id = call_id

    def create(self, data: dict, members: list = None):
        return self._client.get_or_create_call(
            self._call_type, self._call_id, data, members
        )

    def get(self):
        return self._client.get_call(self._call_type, self._call_id)

    def update(self, data: dict):
        return self._client.update_call(self._call_type, self._call_id, data)

    def update_user_permissions(self, data):
        return self._client.update_user_permissions(
            self._call_type, self._call_id, data
        )

    def update_call_members(self, data, members: list = None):
        return self._client.update_call_members(
            self._call_type, self._call_id, data, members
        )

    def unblock_user(self, data):
        return self._client.unblock_user(self._call_type, self._call_id, data)

    def stop_live(self):
        return self._client.stop_live(self._call_type, self._call_id)

    def query_recordings(self, session_id: str = None):
        return self._client.query_recordings(self._call_type, self._call_id, session_id)

    def delete_recording(self, session_id: str, recordingid: str):
        return self._client.delete_recording(
            self._call_type, self._call_id, session_id, recordingid
        )

    def mute_users(self, data):
        return self._client.mute_users(self._call_type, self._call_id, data)

    def query_members(self, data):
        return self._client.query_members(self._call_type, self._call_id, data)

    def request_permissions(self, data):
        return self._client.request_permissions(self._call_type, self._call_id, data)

    def send_custom_event(self, data):
        return self._client.send_custom_event(self._call_type, self._call_id, data)

    def send_reaction(self, data):
        return self._client.send_reaction(self._call_type, self._call_id, data)

    def start_recording(self):
        return self._client.start_recording(self._call_type, self._call_id)

    def start_trancription(self):
        return self._client.start_trancription(self._call_type, self._call_id)

    def start_broadcasting(self):
        return self._client.start_broadcasting(self._call_type, self._call_id)

    def stop_recording(self):
        return self._client.stop_recording(self._call_type, self._call_id)

    def stop_transcription(self):
        return self._client.stop_transcription(self._call_type, self._call_id)

    def stop_broadcasting(self):
        return self._client.stop_broadcasting(self._call_type, self._call_id)

    def block_user(self, data):
        return self._client.block_user(self._call_type, self._call_id, data)

    def end_call(self):
        return self._client.end_call(self._call_type, self._call_id)

    def go_live(self):
        return self._client.go_live(self._call_type, self._call_id)

    def join(self, data):
        return self._client.join_call(self._call_type, self._call_id, data)
