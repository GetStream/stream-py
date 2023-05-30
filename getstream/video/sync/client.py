
from getstream.sync.base import BaseClient
from getstream.video.exceptions import VideoCallTypeBadRequest


class VideoClient(BaseClient):
    def __init__(self, api_key: str, base_url, token,timeout,user_agent):
        super().__init__(api_key=api_key, base_url=base_url, token=token,timeout=timeout,user_agent=user_agent)

    def edges(self):
        response = self.get("/edges")
        json = response.json()
        return json

    def get_edge_server(
        self, calltype: str, callid: str, data
    ) :
        response = self.get(f"/calls/{calltype}/{callid}/get_edge_server", json=data)
        json = response.json()
        return json

    def create_call_type(self, data):
        response = self.post("/calltypes", json=data)
        if response.status_code == 400:
            error_json = response.json()
            message = error_json.pop("message", None)
            code = error_json.pop("code", None)
            status_code = error_json.pop("StatusCode", None)
            raise VideoCallTypeBadRequest(message=message, code = code,status_code=status_code)
        return response.json()

    def get_call_type(self, name: str):
        response = self.get(f"/calltypes/{name}")
        if response.status_code == 400:
            error_json = response.json()
            message = error_json.pop("message", None)
            code = error_json.pop("code", None)
            status_code = error_json.pop("StatusCode", None)
            raise VideoCallTypeBadRequest(message=message, code = code,status_code=status_code)
        return response.json()

    def list_call_types(self):
        response = self.get("/calltypes")
        if response.status_code == 400:
            error_json = response.json()
            message = error_json.pop("message", None)
            code = error_json.pop("code", None)
            status_code = error_json.pop("StatusCode", None)
            raise VideoCallTypeBadRequest(message=message, code = code,status_code=status_code)
        json = response.json()
        return json

    def update_call_type(self, name: str, data):
        response = self.put(f"/calltypes/{name}", json=data)
        if response.status_code == 400:
            error_json = response.json()
            message = error_json.pop("message", None)
            code = error_json.pop("code", None)
            status_code = error_json.pop("StatusCode", None)
            raise VideoCallTypeBadRequest(message=message, code = code,status_code=status_code)
        return response.json()

    def query_calls(self, data):
        response = self.post("/calls", json=data)
        return response.json()

    def block_user(
        self, calltype: str, callid: str,data
    ):
        response = self.post(f"/call/{calltype}/{callid}/block", json=data)
        return response.json()

    def end_call(self, calltype: str, callid: str) :
        response = self.post(f"/call/{calltype}/{callid}/mark_ended")
        return response.json()

    def get_call(self, calltype: str, callid: str):
        response = self.get(f"/call/{calltype}/{callid}")
        return response.json()

    def go_live(self, calltype: str, callid: str):
        response = self.post(f"/call/{calltype}/{callid}/go_live")
        return response.json()

    def join_call(
        self, calltype: str, callid: str, data
    ):
        response = self.post(f"/call/{calltype}/{callid}/join", data=data)
        return response.json()
    
    def delete_call_type(self, name: str):
        response = self.delete(f"/calltypes/{name}")
        if response.status_code == 400:
            error_json = response.json()
            message = error_json.pop("message", None)
            code = error_json.pop("code", None)
            status_code = error_json.pop("StatusCode", None)
            raise VideoCallTypeBadRequest(message=message, code = code,status_code=status_code)
        return response.json()
    
    def delete_recording(
        self, calltype: str, callid: str, sessionid: str, recordingid: str
    ):
        response = self.delete(
            f"/call/{calltype}/{callid}/{sessionid}/recordings/{recordingid}"
        )
        return response.json()

    def list_recordings(
        self, calltype: str, callid: str, sessionid: str
    ):
        response = self.get(f"/call/{calltype}/{callid}/{sessionid}/recordings")
        return response.json()

    def mute_users(
        self, calltype: str, callid: str, data
    ) :
        response = self.post(f"/call/{calltype}/{callid}/mute_users", data=data)
        return response.json()

    def query_members(
        self, calltype: str, callid: str, data
    ) :
        response = self.post(f"/call/{calltype}/{callid}/members", json=data)
        return response.json()

    def request_permission(
        self, calltype: str, callid: str, data
    ) :
        response = self.post(f"/call/{calltype}/{callid}/request_permission", json=data)
        return response.json()

    def send_event(
        self, calltype: str, callid: str, data
    ) :
        response = self.post(f"/call/{calltype}/{callid}/event", json=data)
        return response.json()

    def send_reaction(
        self, calltype: str, callid: str, data
    ) :
        response = self.post(f"/call/{calltype}/{callid}/reaction", json=data)
        return response.json()

    def start_recording(self, calltype: str, callid: str):
        response = self.post(f"/call/{calltype}/{callid}/start_recording")
        return response.json()

    def start_trancription(self, calltype: str, callid: str):
        response = self.post(f"/call/{calltype}/{callid}/start_transcription")
        return response.json()

    def start_broadcasting(self, calltype: str, callid: str):
        response = self.post(f"/call/{calltype}/{callid}/start_broadcasting")
        return response.json()

    def stop_recording(self, calltype: str, callid: str):
        response = self.post(f"/call/{calltype}/{callid}/stop_recording")
        return response.json()

    def stop_transcription(self, calltype: str, callid: str):
        response = self.post(f"/call/{calltype}/{callid}/stop_transcription")
        return response.json()

    def stop_broadcasting(self, calltype: str, callid: str):
        response = self.post(f"/call/{calltype}/{callid}/stop_broadcasting")
        return response.json()

    def stop_live(self, calltype: str, callid: str):
        response = self.post(f"/call/{calltype}/{callid}/stop_live")
        return response.json()

    def unblock_user(
        self, calltype: str, callid: str, data
    ) :
        response = self.post(f"/call/{calltype}/{callid}/unblock", json=data)
        return response.json()

    def update_members(
        self, calltype: str, callid: str, data
    ) :
        response = self.put(f"/call/{calltype}/{callid}/members", json=data)
        return response.json()

    def update_call(
        self, calltype: str, callid: str, data
    ) :
        response = self.put(f"/call/{calltype}/{callid}", json=data)
        return response.json()

    def update_user_permissions(
        self, calltype: str, callid: str, data
    ) :
        response = self.put(f"/call/{calltype}/{callid}/permissions", json=data)
        return response.json()

    def get_or_create_call(
        self, calltype: str, callid: str, data
    ) :
        response = self.post(f"/call/{calltype}/{callid}", json=data)
        return response.json()

    # def call(self, calltype: str, callid: str, data: CallRequest)->Call:
    #     self.currentCall = Call(self.stream, calltype, callid, data)
    #     return self.currentCall
