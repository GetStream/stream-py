import pytest
import os
from dotenv import load_dotenv
from tests.fixtures import client, call, get_user, shared_call

__all__ = ["client", "call", "get_user", "shared_call"]


@pytest.fixture(scope="session", autouse=True)
def load_env():
    load_dotenv()


def pytest_configure(config):
    """Register custom markers."""
    config.addinivalue_line(
        "markers", "skip_in_ci: mark test to skip when running in CI"
    )


def is_running_in_github_actions():
    """Check if the tests are running in GitHub Actions CI."""
    return os.environ.get("GITHUB_ACTIONS") == "true"


def pytest_runtest_setup(item):
    """Skip tests marked with skip_in_ci when running in GitHub Actions."""
    if is_running_in_github_actions():
        skip_in_ci_marker = item.get_closest_marker("skip_in_ci")
        if skip_in_ci_marker is not None:
            pytest.skip("Test skipped in CI environment")
