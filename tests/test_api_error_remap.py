import unittest

from getstream.models import APIError


class TestAPIError(unittest.TestCase):
    def test_from_dict(self):
        # Define a dictionary that simulates the data you receive
        input_data = {
            "StatusCode": 404,
            "code": 12345,
            "details": [1, 2, 3],
            "duration": "1m30s",
            "exception_fields": None,
            "message": "Not found",
            "more_info": "http://more.info.com",
        }

        # Use the static method from_dict() to convert the dict to an APIError instance
        error = APIError.from_dict(input_data)

        # validate the data was loaded correctly
        self.assertEqual(error.status_code, 404)
        self.assertEqual(error.code, 12345)
        self.assertEqual(error.details, [1, 2, 3])
        self.assertEqual(error.duration, "1m30s")
