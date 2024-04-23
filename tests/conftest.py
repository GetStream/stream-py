import pytest
from dotenv import load_dotenv
from tests.fixtures import client, call

__all__ = ["client", "call"]


@pytest.fixture(scope="session", autouse=True)
def load_env():
    load_dotenv()
