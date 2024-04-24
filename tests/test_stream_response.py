from dataclasses_json import DataClassJsonMixin, config
from getstream.models import OwnCapability
from httpx import Response
from datetime import timezone
from dateutil.parser import parse as dt_parse
from getstream.rate_limit import RateLimitInfo
from getstream.stream_response import StreamResponse

from unittest import TestCase
from dataclasses import dataclass, field
from typing import Any, List


@dataclass
class Dummy:
    value: Any


@dataclass
class MockRequest(DataClassJsonMixin):
    own_capabilities: List[OwnCapability] = field(
        metadata=config(field_name="own_capabilities")
    )


class TestStreamResponse(TestCase):
    def setUp(self):
        headers = {
            "x-ratelimit-limit": "100",
            "x-ratelimit-remaining": "80",
            "x-ratelimit-reset": str(
                int(dt_parse("2022-01-01").replace(tzinfo=timezone.utc).timestamp())
            ),
        }
        self.response = Response(200, headers=headers)

        # setup StreamResponse[Dummy]
        self.data = Dummy("SomeValue")
        self.stream_response_dummy = StreamResponse(self.response, self.data)

        # setup StreamResponse[Dict[str, Any]]
        self.data_dict = {"key": "SomeValue"}
        self.stream_response_dict = StreamResponse(self.response, self.data_dict)

    def test_data(self):
        self.assertEqual(self.stream_response_dummy.data.value, "SomeValue")
        self.assertEqual(self.stream_response_dict.data["key"], "SomeValue")

    def test_headers(self):
        self.assertEqual(self.stream_response_dummy.headers(), self.response.headers)
        self.assertEqual(self.stream_response_dict.headers(), self.response.headers)

    def test_status_code(self):
        self.assertEqual(
            self.stream_response_dummy.status_code(), self.response.status_code
        )
        self.assertEqual(
            self.stream_response_dict.status_code(), self.response.status_code
        )

    def test_rate_limit(self):
        rate_limit_dummy = self.stream_response_dummy.rate_limit()
        rate_limit_dict = self.stream_response_dict.rate_limit()

        self.assertIsInstance(rate_limit_dummy, RateLimitInfo)
        self.assertEqual(rate_limit_dummy.limit, 100)
        self.assertEqual(rate_limit_dummy.remaining, 80)
        self.assertEqual(
            rate_limit_dummy.reset, dt_parse("2022-01-01").replace(tzinfo=timezone.utc)
        )

        self.assertIsInstance(rate_limit_dict, RateLimitInfo)
        self.assertEqual(rate_limit_dict.limit, 100)
        self.assertEqual(rate_limit_dict.remaining, 80)
        self.assertEqual(
            rate_limit_dict.reset, dt_parse("2022-01-01").replace(tzinfo=timezone.utc)
        )

    def test_response_with_enum(self):
        obj = MockRequest.from_dict(
            {
                "own_capabilities": ["block-users", "asd"],
            }
        )
        self.assertEqual(obj.own_capabilities, [OwnCapability.BLOCK_USERS, "asd"])
