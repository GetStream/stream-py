from stream.client import BaseClient
from stream.stream import Stream
from stream.model.get_edges_response import GetEdgesResponse
from stream.model.create_call_type_response import CreateCallTypeResponse
from stream.model.get_call_type_response import GetCallTypeResponse
from stream.model.list_call_type_response import ListCallTypeResponse
from stream.model.update_call_type_request import UpdateCallTypeRequest
from stream.model.update_call_type_response import UpdateCallTypeResponse
from stream.model.query_calls_request import QueryCallsRequest
from stream.model.query_calls_response import QueryCallsResponse
from stream.model.create_call_type_request import CreateCallTypeRequest
from stream.model.get_or_create_call_request import GetOrCreateCallRequest
from stream.model.get_or_create_call_response import GetOrCreateCallResponse
from stream.video.call import Call


class Video(BaseClient):
    def __init__(self, stream: Stream):
        self.stream = stream
        self.currentCall = None

        super().__init__(
            self.stream.admin_token, "https://video.stream-io-api.com/video"
        )

    async def edges(self) -> GetEdgesResponse:
        response = await self.stream.get("/edges")
        return GetEdgesResponse(**response.json())

    async def create_call_type(
        self, data: CreateCallTypeRequest
    ) -> CreateCallTypeResponse:
        response = await self.stream.video.post("/calltypes", data=data)
        return CreateCallTypeResponse(**response.json())

    async def get_call_type(self, call_type_id: str) -> GetCallTypeResponse:
        response = await self.stream.video.get(f"/calltypes/{call_type_id}")
        return GetCallTypeResponse(**response.json())

    async def list_call_types(self) -> ListCallTypeResponse:
        response = await self.stream.video.get("/calltypes")
        return ListCallTypeResponse(**response.json())

    async def update_call_type(
        self, name: str, data: UpdateCallTypeRequest
    ) -> UpdateCallTypeResponse:
        response = await self.stream.video.put(f"/calltypes/{name}", data=data)
        return UpdateCallTypeResponse(**response.json())

    async def query_calls(self, data: QueryCallsRequest) -> QueryCallsResponse:
        response = await self.stream.video.post("/calls", data=data)
        return QueryCallsResponse(**response.json())

    async def get_or_create_call(
        self, calltype: str, callid: str, data: GetOrCreateCallRequest
    ) -> GetOrCreateCallResponse:
        response = await self.stream.video.post(
            f"/calls/{calltype}/{callid}", data=data
        )
        return GetOrCreateCallResponse(**response.json())

    def call(self, calltype: str, callid: str, data: dict):
        self.currentCall = Call(self.stream, calltype, callid, data)
