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

    def list_recordings(self, call_type: str, callid: str, sessionid: str):
        response = self.get(f"/call/{call_type}/{callid}/{sessionid}/recordings")
        return response.json()

    def mute_users(self, call_type: str, callid: str, data):
        response = self.post(f"/call/{call_type}/{callid}/mute_users", data=data)
        return response.json()

    def query_members(self, call_type: str, callid: str, data):
        response = self.post(f"/call/{call_type}/{callid}/members", json=data)
        return response.json()

    def request_permission(self, call_type: str, callid: str, data):
        response = self.post(f"/call/{call_type}/{callid}/request_permission", json=data)
        return response.json()

    def send_event(self, call_type: str, callid: str, data):
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

    def update_members(self, call_type: str, callid: str, data):
        response = self.put(f"/call/{call_type}/{callid}/members", json=data)
        return response.json()

    def update_call(self, call_type: str, callid: str, data):
        response = self.put(f"/call/{call_type}/{callid}", json=data)
        return response.json()

    def update_user_permissions(self, call_type: str, callid: str, data):
        response = self.put(f"/call/{call_type}/{callid}/permissions", json=data)
        return response.json()

    def get_or_create_call(self, call_type: str, callid: str, data):
        response = self.post(f"/call/{call_type}/{callid}", json=data)
        return response.json()

    # def call(self, call_type: str, callid: str, data: CallRequest)->Call:
    #     self.currentCall = Call(self.stream, call_type, callid, data)
    #     return self.currentCall
