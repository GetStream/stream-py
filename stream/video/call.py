
import httpx

class Call:
    def __init__(self, stream, endpoint, request_id, data):
        self.stream = stream
        self.endpoint = endpoint
        self.request_id = request_id
        self.data = data

    def get_or_create(self):
        try:
            # Try making a "get" request first
            response = self.stream._make_request(
                "GET",
                f"{self.stream.base_url}/{self.endpoint}/{self.request_id}"
            )
            return response
        except httpx.HTTPStatusError as e:
            if e.response.status_code == 404:  # Not found, so create
                response = self.stream._make_request(
                    "POST",
                    f"{self.stream.base_url}/{self.endpoint}",
                    data=self.data
                )
                return response
            else:
                raise