from stream.model.create_call_type_request import CreateCallTypeRequest
from stream.model.create_call_type_response import CreateCallTypeResponse
from stream.model.get_call_type_response import GetCallTypeResponse
from stream.model.get_edges_response import GetEdgesResponse
from stream.model.get_or_create_call_request import GetOrCreateCallRequest
from stream.model.get_or_create_call_response import GetOrCreateCallResponse
from stream.model.list_call_type_response import ListCallTypeResponse
from stream.model.query_calls_request import QueryCallsRequest
from stream.model.query_calls_response import QueryCallsResponse
from stream.model.update_call_type_request import UpdateCallTypeRequest
from stream.model.update_call_type_response import UpdateCallTypeResponse
from stream.sync.base import BaseClient


class VideoClient(BaseClient):
    def __init__(self, api_key: str, base_url, token):
        super().__init__(api_key=api_key, base_url=base_url, token=token)

    def edges(self) -> GetEdgesResponse:
        response = self.get("/edges")
        json = response.json()
        return GetEdgesResponse(json)

    def create_call_type(self, data: CreateCallTypeRequest) -> CreateCallTypeResponse:
        response = self.post("/calltypes", data=data)
        return CreateCallTypeResponse(**response.json())

    def get_call_type(self, name: str) -> GetCallTypeResponse:
        response = self.get(f"/calltypes/{name}")
        return GetCallTypeResponse(**response.json())

    def list_call_types(self) -> ListCallTypeResponse:
        response = self.get("/calltypes")
        json = response.json()
        return ListCallTypeResponse(json)

    def update_call_type(
        self, name: str, data: UpdateCallTypeRequest
    ) -> UpdateCallTypeResponse:
        response = self.put(f"/calltypes/{name}", data=data)
        return UpdateCallTypeResponse(**response.json())

    def query_calls(self, data: QueryCallsRequest) -> QueryCallsResponse:
        response = self.post("/calls", data=data)
        return QueryCallsResponse(**response.json())

    def get_or_create_call(
        self, calltype: str, callid: str, data: GetOrCreateCallRequest
    ) -> GetOrCreateCallResponse:
        response = self.post(f"/calls/{calltype}/{callid}", data=data)
        return GetOrCreateCallResponse(**response.json())

    # def call(self, calltype: str, callid: str, data: CallRequest)->Call:
    #     self.currentCall = Call(self.stream, calltype, callid, data)
    #     return self.currentCall
