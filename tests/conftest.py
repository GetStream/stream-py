import pytest
from dotenv import load_dotenv
from tests.fixtures import client, call, get_user

__all__ = ["client", "call", "get_user"]


@pytest.fixture(scope="session", autouse=True)
def load_env():
    load_dotenv()
