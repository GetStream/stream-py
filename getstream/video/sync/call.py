from getstream.video.sync.client import VideoClient


class Call:
    def __init__(self, client: VideoClient, call_type: str, callid: str):
        self._client = client
        self._call_type = call_type
        self._callid = callid

    def create(self, data):
        return self._client.get_or_create_call(self._call_type, self._callid, data)

    def get(self):
        return self._client.get_call(self._call_type, self._callid)

    def update(self, data):
        return self._client.update_call(self._call_type, self._callid, data)

    def update_user_permissions(self, data):
        return self._client.update_user_permissions(self._call_type, self._callid, data)

    def update_call_members(self, data):
        return self._client.update_call_members(self._call_type, self._callid, data)

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
