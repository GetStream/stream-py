import json
from typing import Dict, Optional

from getstream.models.api_error import ApiError
from getstream.rate_limit import extract_rate_limit


class StreamAPIException(Exception):
    def __init__(self, response: str) -> None:
        self.api_error: Optional[ApiError] = None
        self.rate_limit_info = extract_rate_limit(response)

        try:
            parsed_response: Dict = json.loads(response.text)
            self.api_error = ApiError.from_dict(parsed_response)
        except ValueError:
            pass

    def __str__(self) -> str:
        if self.api_error:
            return f'Stream error code {self.api_error.code}: {self.api_error.message}"'
        else:
            return f"Stream error HTTP code: {self.status_code}"
