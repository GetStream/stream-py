from stream.model.call_type_response import CallTypeResponse
from stream.sync import Stream

client = Stream(
    api_key="your-api-key",
    api_secret="your-secret",
)

print(client.create_token(role="admin"))
call_types: CallTypeResponse = client.video.list_call_types().call_types

for type in call_types:
    print(type)
