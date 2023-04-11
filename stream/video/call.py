


from stream.model.get_or_create_call_response import GetOrCreateCallResponse
from stream.stream import Stream

class Call:
    def __init__(self, stream: Stream, call_type: str, call_id: str, data: dict):
        self.stream = stream
        self.call_type = call_type
        self.call_id = call_id
        self.data = data
        self.members = None
        self.blocked_users = None
        

    async def get_or_create(self)-> GetOrCreateCallResponse:
        response = await self.stream.video.get_or_create_call(self.call_type, self.call_id, self.data)
        self.members= response.members
        self.blocked_users= response.blocked_users
        self.call = response.call
        return response

