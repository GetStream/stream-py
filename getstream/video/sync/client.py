from getstream.sync.base import BaseClient
from getstream.video.exceptions import VideoCallTypeBadRequest


class VideoClient(BaseClient):
    def __init__(self, api_key: str, base_url, token, timeout, user_agent):
        """
        Initializes VideoClient with BaseClient instance
        :param api_key: A string representing the client's API key
        :param base_url: A string representing the base uniform resource locator
        :param token: A string instance representing the client's token
        :param timeout: A number representing the time limit for a request
        :param user_agent: A string representing the user agent
        """
        super().__init__(
            api_key=api_key,
            base_url=base_url,
            token=token,
            timeout=timeout,
            user_agent=user_agent,
        )

    def call(self, call_type: str, call_id: str):
        """
        Returns instance of Call class
        :param call_type: A string representing the call type
        :param call_id: A string representing a unique call identifier
        :return: Instance of Call class
        """
        return Call(self, call_type, call_id)

    def edges(self):
        """
        Retrieves edges from the server
        :return: json object with response
        """
        response = self.get("/edges")
        json = response.json()
        return json

    def get_edge_server(self, call_type: str, call_id: str, data):
        """
        Retrieves specific edge server
        :param call_type: A string representing the call type
        :param call_id: A string representing a unique call identifier
        :param data: A dictionary with additional call details
        :return: json object with response
        """
        response = self.get(f"/calls/{call_type}/{call_id}/get_edge_server", json=data)
        json = response.json()
        return json

    def create_call_type(self, data):
        """
        Creates a new call type
        :param data: A dictionary with details about the call type
        :return: json object with response
        """
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
        """
        Retrieves specific call type
        :param name: A string representing the name of the call type
        :return: json object with response
        """
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
        """
        Returns a list with all call types of the client
        :return: json object with response
        """
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
        """
        Updates specific call type
        :param name: A string representing the name of the call type
        :param data: A dictionary with details about the call type
        :return: json object with response
        """
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
        """
        Executes a query about specific call
        :param data: A dictionary with additional call details
        :return: json object with response
        """
        response = self.post("/calls", json=data)
        return response.json()

    def block_user(self, call_type: str, call_id: str, data):
        """
        Blocks user in specific call
        :param call_type: A string representing the call type
        :param call_id: A string representing a unique call identifier
        :param data: A dictionary with additional call details
        :return: json object with response
        """
        response = self.post(f"/call/{call_type}/{call_id}/block", json=data)
        return response.json()

    def end_call(self, call_type: str, call_id: str):
        """
        Ends specific call
        :param call_type: A string representing the call type
        :param call_id: A string representing a unique call identifier
        :return: json object with response
        """
        response = self.post(f"/call/{call_type}/{call_id}/mark_ended")
        return response.json()

    def get_call(self, call_type: str, call_id: str):
        """
        Retrieves specific call
        :param call_type: A string representing the call type
        :param call_id: A string representing a unique call identifier
        :return: json object with response
        """
        response = self.get(f"/call/{call_type}/{call_id}")
        return response.json()

    def go_live(self, call_type: str, call_id: str):
        """
        Makes specific call go live
        :param call_type: A string representing the call type
        :param call_id: A string representing a unique call identifier
        :return: json object with response
        """
        response = self.post(f"/call/{call_type}/{call_id}/go_live")
        return response.json()

    def join_call(self, call_type: str, call_id: str, data):
        """
        Joins specific call
        :param call_type: A string representing the call type
        :param call_id: A string representing a unique call identifier
        :param data: A dictionary with additional call details
        :return: json object with response
        """
        response = self.post(f"/call/{call_type}/{call_id}/join", data=data)
        return response.json()

    def delete_call_type(self, name: str):
        """
        Deletes specific call type
        :param name: A string representing the name of the call type
        :return: json object with response
        """
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
        """
        Deletes specific recording of a call
        :param call_type: A string representing the call type
        :param call_id: A string representing a unique call identifier
        :param session_id: A string representing a unique session identifier
        :param recordingid: A string representing a unique recording identifier
        :return: json object with response
        """
        response = self.delete(
            f"/call/{call_type}/{call_id}/{session_id}/recordings/{recordingid}"
        )
        return response.json()

    def add_device(
        self, id, push_provider, push_provider_name=None, user_id=None, voip_token=None
    ):
        """
        Adds device to the client
        :param id: A string representing device identifier
        :param push_provider: An instance representing the push provider
        :param push_provider_name: A string representing the name of the push provider
        :param user_id: A string representing a unique user identifier
        :param voip_token: A string representing the Voice Over IP token
        :return: json object with response
        """
        data = {"id": id, "push_provider": push_provider, "voip_token": voip_token}
        if user_id is not None:
            data.update({"user_id": user_id})
        if push_provider_name is not None:
            data.update({"push_provider_name": push_provider_name})
        response = self.post("/devices", json=data)
        return response.json()

    def add_voip_device(self, id, push_provider, push_provider_name=None, user_id=None):
        """
        Adds Voice Over IP device to the client
        :param id: A string representing device identifier
        :param push_provider: An instance representing the push provider
        :param push_provider_name: A string representing the name of the push provider
        :param user_id: A string representing a unique user identifier
        """
        self.add_device(id, push_provider, push_provider_name, user_id, voip_token=True)

    def get_devices(self):
        """
        Retrieves all devices of the client
        :return: json object with response
        """
        response = self.get("/devices")
        return response.json()

    def remove_device(self, data):
        """
        Removes specific device from the client
        :param data: A dictionary with additional details about the device
        :return: json object with response
        """
        response = self.delete("/devices", json=data)
        return response.json()

    def query_recordings(self, call_type: str, call_id: str, session_id: str = None):
        """
        Executes a query to retrieve specific call recordings
        :param call_type: A string representing the call type
        :param call_id: A string representing a unique call identifier
        :param session_id: A string representing a unique session identifier
        :return: json object with response
        """
        if session_id is None:
            response = self.get(f"/call/{call_type}/{call_id}/recordings")
        response = self.get(f"/call/{call_type}/{call_id}/{session_id}/recordings")
        return response.json()

    def mute_users(self, call_type: str, call_id: str, data):
        """
        Mute users in a specific call
        :param call_type: A string representing the call type
        :param call_id: A string representing a unique call identifier
        :param data: A dictionary with additional call details
        :return: json object with response
        """
        response = self.post(f"/call/{call_type}/{call_id}/mute_users", data=data)
        return response.json()

    def query_members(self, call_type: str, call_id: str, data):
        """
        Executes a query to retrieve specific call members
        :param call_type: A string representing the call type
        :param call_id: A string representing a unique call identifier
        :param data: A dictionary with additional call details
        :return: json object with response
        """
        response = self.post(f"/call/{call_type}/{call_id}/members", json=data)
        return response.json()

    def request_permissions(self, call_type: str, call_id: str, data):
        """
        Requests permissions for a specific call
        :param call_type: A string representing the call type
        :param call_id: A string representing a unique call identifier
        :param data: A dictionary with additional call details
        :return: json object with response
        """
        response = self.post(
            f"/call/{call_type}/{call_id}/request_permission", json=data
        )
        return response.json()

    def send_custom_event(self, call_type: str, call_id: str, data):
        """
        Sends a custom event for a specific call
        :param call_type: A string representing the call type
        :param call_id: A string representing a unique call identifier
        :param data: A dictionary with additional call details
        :return: json object with response
        """
        response = self.post(f"/call/{call_type}/{call_id}/event", json=data)
        return response.json()

    def send_reaction(self, call_type: str, call_id: str, data):
        """
        Sends a reaction for a specific call
        :param call_type: A string representing the call type
        :param call_id: A string representing a unique call identifier
        :param data: A dictionary with additional call details
        :return: json object with response
        """
        response = self.post(f"/call/{call_type}/{call_id}/reaction", json=data)
        return response.json()

    def start_recording(self, call_type: str, call_id: str):
        """
        Starts recording for a specific call
        :param call_type: A string representing the call type
        :param call_id: A string representing a unique call identifier
        :return: json object with response
        """
        response = self.post(f"/call/{call_type}/{call_id}/start_recording")
        return response.json()

    def start_trancription(self, call_type: str, call_id: str):
        """
        Starts transcription for a specific call
        :param call_type: A string representing the call type
        :param call_id: A string representing a unique call identifier
        :return: json object with response
        """
        response = self.post(f"/call/{call_type}/{call_id}/start_transcription")
        return response.json()

    def start_broadcasting(self, call_type: str, call_id: str):
        """
        Starts broadcasting for a specific call
        :param call_type: A string representing the call type
        :param call_id: A string representing a unique call identifier
        :return: json object with response
        """
        response = self.post(f"/call/{call_type}/{call_id}/start_broadcasting")
        return response.json()

    def stop_recording(self, call_type: str, call_id: str):
        """
        Stops recording for a specific call
        :param call_type: A string representing the call type
        :param call_id: A string representing a unique call identifier
        :return: json object with response
        """
        response = self.post(f"/call/{call_type}/{call_id}/stop_recording")
        return response.json()

    def stop_transcription(self, call_type: str, call_id: str):
        """
        Stops transcription for a specific call
        :param call_type: A string representing the call type
        :param call_id: A string representing a unique call identifier
        :return: json object with response
        """
        response = self.post(f"/call/{call_type}/{call_id}/stop_transcription")
        return response.json()

    def stop_broadcasting(self, call_type: str, call_id: str):
        """
        Stops broadcasting for a specific call
        :param call_type: A string representing the call type
        :param call_id: A string representing a unique call identifier
        :return: json object with response
        """
        response = self.post(f"/call/{call_type}/{call_id}/stop_broadcasting")
        return response.json()

    def stop_live(self, call_type: str, call_id: str):
        """
        Stops the live status of a call
        :param call_type: A string representing the call type
        :param call_id: A string representing a unique call identifier
        :return: json object with response
        """
        response = self.post(f"/call/{call_type}/{call_id}/stop_live")
        return response.json()

    def unblock_user(self, call_type: str, call_id: str, data):
        """
        Unblocks a user from a specific call
        :param call_type: A string representing the call type
        :param call_id: A string representing a unique call identifier
        :param data: A dictionary with additional call details
        :return: json object with response
        """
        response = self.post(f"/call/{call_type}/{call_id}/unblock", json=data)
        return response.json()

    def update_call_members(self, call_type: str, call_id: str, members: list = None):
        """
        Updates the members of a specific call
        :param call_type: A string representing the call type
        :param call_id: A string representing a unique call identifier
        :param members: A list with the members' details
        :return: json object with response
        """
        data = {"update_members": members}
        response = self.put(f"/call/{call_type}/{call_id}/members", json=data)
        return response.json()

    def update_call(self, call_type: str, call_id: str, data):
        """
        Updates a specific call
        :param call_type: A string representing the call type
        :param call_id: A string representing a unique call identifier
        :param data: A dictionary with additional call details
        :return: json object with response
        """
        request_data = {"data": data}
        response = self.put(f"/call/{call_type}/{call_id}", json=request_data)
        return response.json()

    def update_user_permissions(self, call_type: str, call_id: str, data):
        """
        Updates user permissions for a specific call
        :param call_type: A string representing the call type
        :param call_id: A string representing a unique call identifier
        :param data: A dictionary with additional call details
        :return: json object with response
        """
        response = self.put(f"/call/{call_type}/{call_id}/permissions", json=data)
        return response.json()

    def get_or_create_call(
        self, call_type: str, call_id: str, data: dict, members: list = None
    ):
        """
        Returns a specific call and creates one if it does not exist
        :param call_type: A string representing the call type
        :param call_id: A string representing a unique call identifier
        :param data: A dictionary with additional call details
        :param members: A list with the call members' details
        :return: json object with response
        """
        request_data = {"data": data}
        if members is not None:
            request_data.update({"members": members})
        response = self.post(f"/call/{call_type}/{call_id}", json=request_data)
        return response.json()


class Call:
    def __init__(self, client: VideoClient, call_type: str, call_id: str):
        """
        Initializes Call with VideoClient instance
        :param client: An instance of VideoClient class
        :param call_type: A string representing the call type
        :param call_id: A string representing a unique call identifier
        """
        self._client = client
        self._call_type = call_type
        self._call_id = call_id

    def create(self, data: dict, members: list = None):
        """
        Creates a call with given data and members
        :param data: A dictionary with call details
        :param members: A list of members to be included in the call
        :return: Response from the create call API
        """
        return self._client.get_or_create_call(
            self._call_type, self._call_id, data, members
        )

    def get(self):
        """
        Retrieves the call based on call type and id
        :return: Response from the get call API
        """
        return self._client.get_call(self._call_type, self._call_id)

    def update(self, data: dict):
        """
        Updates the call with given data
        :param data: A dictionary with updated call details
        :return: Response from the update call API
        """
        return self._client.update_call(self._call_type, self._call_id, data)

    def update_user_permissions(self, data):
        """
        Updates permissions of the user in the call
        :param data: A dictionary with permission details
        :return: Response from the update user permissions API
        """
        return self._client.update_user_permissions(
            self._call_type, self._call_id, data
        )

    def update_call_members(self, members: list = None):
        """
        Updates members of the call
        :param members: A list of new members to be included in the call
        :return: Response from the update call members API
        """
        return self._client.update_call_members(self._call_type, self._call_id, members)

    def unblock_user(self, data):
        """
        Unblocks user from the call
        :param data: A dictionary with user details
        :return: Response from the unblock user API
        """
        return self._client.unblock_user(self._call_type, self._call_id, data)

    def stop_live(self):
        """
        Stops live call
        :return: Response from the stop live API
        """
        return self._client.stop_live(self._call_type, self._call_id)

    def query_recordings(self, session_id: str = None):
        """
        Executes a query to retrieve recordings of the call
        :param session_id: A string representing a unique session identifier
        :return: Response from the query recordings API
        """
        return self._client.query_recordings(self._call_type, self._call_id, session_id)

    def delete_recording(self, session_id: str, recordingid: str):
        """
        Deletes specific recording of the call
        :param session_id: A string representing a unique session identifier
        :param recordingid: A string representing a unique recording identifier
        :return: Response from the delete recording API
        """
        return self._client.delete_recording(
            self._call_type, self._call_id, session_id, recordingid
        )

    def mute_users(self, data):
        """
        Mute users in the call
        :param data: A dictionary with user details
        :return: Response from the mute users API
        """
        return self._client.mute_users(self._call_type, self._call_id, data)

    def query_members(self, data):
        """
        Executes a query to retrieve members of the call
        :param data: A dictionary with query details
        :return: Response from the query members API
        """
        return self._client.query_members(self._call_type, self._call_id, data)

    def request_permissions(self, data):
        """
        Requests permissions for the call
        :param data: A dictionary with permission details
        :return: Response from the request permissions API
        """
        return self._client.request_permissions(self._call_type, self._call_id, data)

    def send_custom_event(self, data):
        """
        Sends a custom event for the call
        :param data: A dictionary with event details
        :return: Response from the send custom event API
        """
        return self._client.send_custom_event(self._call_type, self._call_id, data)

    def send_reaction(self, data):
        """
        Sends a reaction for the call
        :param data: A dictionary with reaction details
        :return: Response from the send
        """
        return self._client.send_reaction(self._call_type, self._call_id, data)

    def start_recording(self):
        """
        Starts recording for the call
        :return: Response from the start recording API
        """
        return self._client.start_recording(self._call_type, self._call_id)

    def start_trancription(self):
        """
        Starts transcription for the call
        :return: Response from the start transcription API
        """
        return self._client.start_trancription(self._call_type, self._call_id)

    def start_broadcasting(self):
        """
        Starts broadcasting for the call
        :return: Response from the start broadcasting API
        """
        return self._client.start_broadcasting(self._call_type, self._call_id)

    def stop_recording(self):
        """
        Stops recording for the call
        :return: Response from the stop recording API
        """
        return self._client.stop_recording(self._call_type, self._call_id)

    def stop_transcription(self):
        """
        Stops transcription for the call
        :return: Response from the stop transcription API
        """
        return self._client.stop_transcription(self._call_type, self._call_id)

    def stop_broadcasting(self):
        """
        Stops broadcasting for the call
        :return: Response from the stop broadcasting API
        """
        return self._client.stop_broadcasting(self._call_type, self._call_id)

    def block_user(self, data):
        """
        Blocks user in the call
        :param data: A dictionary with user details
        :return: Response from the block user API
        """
        return self._client.block_user(self._call_type, self._call_id, data)

    def end_call(self):
        """
        Ends the call
        :return: Response from the end call API
        """
        return self._client.end_call(self._call_type, self._call_id)

    def go_live(self):
        """
        Makes the call go live
        :return: Response from the go live API
        """
        return self._client.go_live(self._call_type, self._call_id)

    def join(self, data):
        """
        Joins the call
        :param data: A dictionary with user details
        :return: Response from the join call API
        """
        return self._client.join_call(self._call_type, self._call_id, data)
