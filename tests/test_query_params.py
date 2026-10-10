import httpx

from getstream import Stream


class Recorder:
    def __init__(self):
        self.requests = []

    def __call__(self, request: httpx.Request) -> httpx.Response:
        self.requests.append(request)
        return httpx.Response(200, json={"duration": "0ms", "collections": []})


REFS = ["food:pizza", "user@example.com", "a b"]


def test_list_query_params_are_encoded_once():
    recorder = Recorder()
    client = Stream(
        api_key="key", api_secret="secret", transport=httpx.MockTransport(recorder)
    )

    client.feeds.read_collections(collection_refs=REFS)

    (request,) = recorder.requests
    assert request.url.params["collection_refs"] == ",".join(REFS)
