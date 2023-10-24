import unittest

from getstream.models.user_request import UserRequest
from getstream.models.user_response import UserResponse
from getstream.utils import from_chat_user_dict, to_chat_user_dict


class TestCompatUtils(unittest.TestCase):
    def setUp(self):

        self.user_request = UserRequest(
            id="123",
            name="John Doe",
            role="admin",
            teams=["dev", "marketing"],
            custom={"location": "New York", "age": 30},
        )

        self.user_response = UserResponse(
            id="123",
            name="John Doe",
            role="admin",
            teams=["dev", "marketing"],
            created_at="2021-01-01T00:00:00.000000Z",
            updated_at="2021-01-01T00:00:00.000000Z",
            custom={"location": "New York", "age": 30},
        )

    def test_to_chat_user_dict(self):
        chat_user_dict = to_chat_user_dict(self.user_request)
        expected_dict = {
            "id": "123",
            "name": "John Doe",
            "role": "admin",
            "teams": ["dev", "marketing"],
            "image": None,
            "location": "New York",
            "age": 30,
        }
        self.assertEqual(chat_user_dict, expected_dict)

    def test_from_chat_user_dict(self):
        # 'role', 'teams', 'updated_at', and 'created_at'
        chat_user_dict = {
            "id": "123",
            "role": "admin",
            "teams": ["dev", "marketing"],
            "created_at": "2021-01-01T00:00:00.000000Z",
            "updated_at": "2021-01-01T00:00:00.000000Z",
            "name": "John Doe",
            "location": "New York",
            "age": 30,
        }
        user_response = from_chat_user_dict(chat_user_dict)
        self.assertEqual(user_response.id, "123")

        self.assertEqual(
            user_response.custom,
            {"location": "New York", "age": 30},
        )


if __name__ == "__main__":
    unittest.main()
